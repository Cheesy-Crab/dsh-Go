package io.github.ccch1mneyyy.dsh_app.health

import android.content.Context
import android.util.Log
import java.security.SecureRandom

/**
 * 健康模块入口（fork 新增）。
 *
 * 启动时机：由 [HealthBootstrapProvider] 在进程启动时自动调用，
 * 不修改上游的 Application / MainActivity。
 *
 * 职责：
 *   1. 生成并保存本地接口的访问 token（首次启动一次）
 *   2. 起回环 HTTP 服务
 *   3. 持有 BLE 连接器（目前是占位实现）
 */
object HealthRuntime {
    private const val TAG = "DshHealth"
    private const val PREFS = "dsh_health"
    private const val KEY_TOKEN = "http_token"

    @Volatile
    private var started = false

    @Volatile
    private var server: HealthHttpServer? = null

    @Volatile
    private var store: HealthStore? = null

    @Volatile
    private var connector: HealthBleConnector? = null

    fun ensureStarted(context: Context) {
        if (started) return
        synchronized(this) {
            if (started) return
            val app = context.applicationContext
            val token = tokenOf(app)
            val db = HealthStore(app)
            val ble = StubBleConnector()
            ble.start()
            val http = HealthHttpServer(token = token, store = db, connector = ble)
            try {
                http.start()
                Log.i(TAG, "健康本地接口已启动：127.0.0.1:${HealthHttpServer.DEFAULT_PORT}")
            } catch (error: Exception) {
                // 端口被占用不该影响 App 主流程
                Log.w(TAG, "健康本地接口启动失败：${error.message}")
            }
            store = db
            connector = ble
            server = http
            started = true
        }
    }

    /** 给设置页用：当前本地接口的 token（用户复制进插件配置）。 */
    fun token(context: Context): String = tokenOf(context.applicationContext)

    fun isConnected(): Boolean = connector?.status()?.connected == true

    fun stop() {
        server?.stop()
        connector?.stop()
        store?.close()
        server = null
        connector = null
        store = null
        started = false
    }

    private fun tokenOf(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        prefs.getString(KEY_TOKEN, null)?.let { if (it.length >= 32) return it }
        val bytes = ByteArray(24)
        SecureRandom().nextBytes(bytes)
        val token = bytes.joinToString("") { "%02x".format(it) }
        prefs.edit().putString(KEY_TOKEN, token).apply()
        return token
    }
}
