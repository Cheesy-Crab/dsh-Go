package io.github.ccch1mneyyy.dsh_app.health

/**
 * BLE 连接层接口（fork 新增）。
 *
 * 现在只有占位实现：真正的协议实现（认证握手 / 订阅心率 / 拉活动数据）
 * 等协议细节确认后填进来，接口保持不变，HTTP 服务不用改。
 */
interface HealthBleConnector {
    fun status(): BleStatus

    /** 请求立刻从手环拉一次数据；实现方自行决定是否合并进行中的请求。 */
    fun requestSync()

    fun start()

    fun stop()
}

data class BleStatus(
    val connected: Boolean,
    val bandName: String? = null,
    val battery: Int? = null,
    val keyConfigured: Boolean = false,
    val lastSampleAt: String? = null
)

/**
 * 占位实现：永远「未连接」。
 *
 * 这样 HTTP 服务可以先跑起来、契约可以先对接；
 * 手环没接上时插件会收到 409 / connected=false，行为是明确的。
 */
class StubBleConnector : HealthBleConnector {
    override fun status(): BleStatus = BleStatus(
        connected = false,
        bandName = null,
        battery = null,
        keyConfigured = false,
        lastSampleAt = null
    )

    override fun requestSync() {
        // 没有真实连接时什么也不做；插件侧会看到状态仍是未连接
    }

    override fun start() = Unit

    override fun stop() = Unit
}
