package io.github.ccch1mneyyy.dsh_app.health

import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedInputStream
import java.io.BufferedOutputStream
import java.io.InputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.util.concurrent.Executors

/**
 * 回环 HTTP 服务：把本地健康数据暴露给 DSH 插件（fork 新增）。
 *
 * 契约见 dsh-health 仓库的 docs/ble-contract.md：
 *   GET  /v1/health/summary?date=…   一天的完整摘要
 *   GET  /v1/health/range?days=&end=  近 N 天日聚合
 *   GET  /v1/health/status            连接状态
 *   POST /v1/health/sync              请求立刻同步
 *
 * 只绑 127.0.0.1；鉴权用恒定时间比较，避免时序侧信道。
 */
class HealthHttpServer(
    private val token: String,
    private val store: HealthStore,
    private val connector: HealthBleConnector,
    private val port: Int = DEFAULT_PORT
) {
    private var serverSocket: ServerSocket? = null
    private val pool = Executors.newFixedThreadPool(4) { runnable ->
        Thread(runnable, "dsh-health-http").apply { isDaemon = true }
    }

    @Volatile
    private var running = false

    fun start() {
        if (running) return
        val socket = ServerSocket(port, 8, InetAddress.getByName("127.0.0.1"))
        serverSocket = socket
        running = true
        Thread({ acceptLoop(socket) }, "dsh-health-accept").apply { isDaemon = true }.start()
    }

    fun stop() {
        running = false
        runCatching { serverSocket?.close() }
        pool.shutdownNow()
    }

    private fun acceptLoop(socket: ServerSocket) {
        while (running) {
            val client = try {
                socket.accept()
            } catch (_: Exception) {
                if (running) continue else break
            }
            pool.execute { handle(client) }
        }
    }

    private fun handle(client: Socket) {
        client.use { socket ->
            socket.soTimeout = 5_000
            val input = BufferedInputStream(socket.getInputStream())
            val output = BufferedOutputStream(socket.getOutputStream())

            val requestLine = readLine(input) ?: return
            val parts = requestLine.split(' ')
            if (parts.size < 2) {
                respond(output, 400, errorBody("bad-request"))
                return
            }
            val method = parts[0].uppercase()
            val target = parts[1]

            val headers = HashMap<String, String>()
            while (true) {
                val line = readLine(input) ?: break
                if (line.isEmpty()) break
                val idx = line.indexOf(':')
                if (idx > 0) headers[line.substring(0, idx).trim().lowercase()] = line.substring(idx + 1).trim()
            }

            if (!authorized(headers["authorization"])) {
                respond(output, 401, errorBody("unauthorized"))
                return
            }

            val (path, query) = splitTarget(target)

            when {
                path == "/v1/health/summary" && method == "GET" -> {
                    val date = query["date"] ?: today()
                    respond(output, 200, summaryJson(date))
                }

                path == "/v1/health/range" && method == "GET" -> {
                    val days = (query["days"]?.toIntOrNull() ?: 7).coerceIn(1, 30)
                    val end = query["end"] ?: today()
                    respond(output, 200, rangeJson(days, end))
                }

                path == "/v1/health/status" && method == "GET" -> {
                    respond(output, 200, statusJson())
                }

                path == "/v1/health/sync" && method == "POST" -> {
                    connector.requestSync()
                    respond(output, 200, JSONObject().apply {
                        put("ok", true)
                        put("requestedAt", java.time.Instant.now().toString())
                    })
                }

                else -> respond(output, 404, errorBody("not-found"))
            }
        }
    }

    private fun authorized(header: String?): Boolean {
        val expected = "Bearer $token".toByteArray(StandardCharsets.UTF_8)
        val actual = (header ?: "").toByteArray(StandardCharsets.UTF_8)
        // 长度不同也要走完整比较，避免泄漏长度信息
        return actual.size == expected.size && MessageDigest.isEqual(actual, expected)
    }

    private fun summaryJson(date: String): JSONObject {
        val day = store.summary(date)
        val hours = JSONArray()
        store.hours(date).forEach { h ->
            hours.put(JSONObject().apply {
                put("hour", h.hour)
                if (h.avg != null) put("avg", h.avg) else put("avg", JSONObject.NULL)
                if (h.min != null) put("min", h.min) else put("min", JSONObject.NULL)
                if (h.max != null) put("max", h.max) else put("max", JSONObject.NULL)
            })
        }
        return JSONObject().apply {
            put("date", day.date)
            put("steps", day.steps)
            put("distanceM", day.distanceM)
            put("calories", day.calories)
            put("activeMin", day.activeMin)
            put("sleep", JSONObject().apply {
                put("totalMin", day.sleepTotalMin)
                put("deepMin", day.sleepDeepMin)
                put("remMin", day.sleepRemMin)
                put("lightMin", day.sleepLightMin)
                put("awakeMin", day.sleepAwakeMin)
            })
            put("hr", JSONObject().apply {
                if (day.restingHr != null) put("resting", day.restingHr) else put("resting", JSONObject.NULL)
                if (day.avgHr != null) put("avg", day.avgHr) else put("avg", JSONObject.NULL)
                put("hours", hours)
            })
            put("updatedAt", store.meta("last_sync_at") ?: JSONObject.NULL)
        }
    }

    private fun rangeJson(days: Int, endDate: String): JSONObject {
        val list = JSONArray()
        store.range(days, endDate).forEach { day ->
            list.put(JSONObject().apply {
                put("date", day.date)
                put("steps", day.steps)
                put("distanceM", day.distanceM)
                put("calories", day.calories)
                put("activeMin", day.activeMin)
                put("sleepMin", day.sleepTotalMin)
                if (day.restingHr != null) put("restingHr", day.restingHr) else put("restingHr", JSONObject.NULL)
            })
        }
        return JSONObject().put("days", list)
    }

    private fun statusJson(): JSONObject {
        val status = connector.status()
        return JSONObject().apply {
            put("connected", status.connected)
            put("bandName", status.bandName ?: JSONObject.NULL)
            put("battery", if (status.battery != null) status.battery else JSONObject.NULL)
            put("keyConfigured", status.keyConfigured)
            put("lastSampleAt", status.lastSampleAt ?: JSONObject.NULL)
        }
    }

    private fun errorBody(code: String) = JSONObject().put("error", code)

    private fun respond(output: BufferedOutputStream, status: Int, body: JSONObject) {
        val bytes = body.toString().toByteArray(StandardCharsets.UTF_8)
        val head = buildString {
            append("HTTP/1.1 ").append(status).append(" ").append(reason(status)).append("\r\n")
            append("Content-Type: application/json; charset=utf-8\r\n")
            append("Content-Length: ").append(bytes.size).append("\r\n")
            append("Connection: close\r\n\r\n")
        }.toByteArray(StandardCharsets.UTF_8)
        output.write(head)
        output.write(bytes)
        output.flush()
    }

    private fun reason(status: Int) = when (status) {
        200 -> "OK"
        400 -> "Bad Request"
        401 -> "Unauthorized"
        404 -> "Not Found"
        else -> "Internal Server Error"
    }

    private fun splitTarget(target: String): Pair<String, Map<String, String>> {
        val idx = target.indexOf('?')
        if (idx < 0) return target to emptyMap()
        val path = target.substring(0, idx)
        val query = target.substring(idx + 1).split('&').mapNotNull { pair ->
            val eq = pair.indexOf('=')
            if (eq <= 0) null
            else decode(pair.substring(0, eq)) to decode(pair.substring(eq + 1))
        }.toMap()
        return path to query
    }

    private fun decode(value: String): String =
        runCatching { java.net.URLDecoder.decode(value, "UTF-8") }.getOrDefault(value)

    private fun readLine(input: InputStream): String? {
        val buffer = StringBuilder()
        while (true) {
            val b = input.read()
            if (b == -1) return if (buffer.isEmpty()) null else buffer.toString()
            if (b == '\n'.code) return buffer.toString().trimEnd('\r')
            buffer.append(b.toChar())
            if (buffer.length > 8192) return null // 防止畸形请求无限读
        }
    }

    private fun today(): String = java.time.LocalDate.now().toString()

    companion object {
        const val DEFAULT_PORT = 18765
    }
}
