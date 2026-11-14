package io.github.ccch1mneyyy.dsh_app.health

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

/**
 * 健康数据本地库（fork 新增，不修改上游文件）。
 *
 * 表结构与插件侧的 health.db 保持一致：
 *   daily    —— 日聚合
 *   hr_hour  —— 小时级心率（原始采样不落盘）
 *   sleep    —— 睡眠阶段
 *   meta     —— 同步状态
 *
 * 插件通过本地 HTTP 接口读这里的聚合结果，不直接读库。
 */
class HealthStore(context: Context) : SQLiteOpenHelper(context.applicationContext, DB_NAME, null, DB_VERSION) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS daily (
              date TEXT PRIMARY KEY,
              steps INTEGER NOT NULL DEFAULT 0,
              distance_m INTEGER NOT NULL DEFAULT 0,
              calories INTEGER NOT NULL DEFAULT 0,
              active_min INTEGER NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL
            )
            """.trimIndent()
        )
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS hr_hour (
              date TEXT NOT NULL,
              hour INTEGER NOT NULL,
              avg INTEGER,
              min INTEGER,
              max INTEGER,
              PRIMARY KEY (date, hour)
            )
            """.trimIndent()
        )
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS sleep (
              date TEXT PRIMARY KEY,
              total_min INTEGER NOT NULL DEFAULT 0,
              deep_min INTEGER NOT NULL DEFAULT 0,
              rem_min INTEGER NOT NULL DEFAULT 0,
              light_min INTEGER NOT NULL DEFAULT 0,
              awake_min INTEGER NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL
            )
            """.trimIndent()
        )
        db.execSQL("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // 目前只有 v1；以后加字段时在这里做迁移，不要 DROP（会丢历史数据）
    }

    fun upsertDaily(date: String, steps: Int, distanceM: Int, calories: Int, activeMin: Int) {
        val values = ContentValues().apply {
            put("date", date)
            put("steps", steps.coerceAtLeast(0))
            put("distance_m", distanceM.coerceAtLeast(0))
            put("calories", calories.coerceAtLeast(0))
            put("active_min", activeMin.coerceAtLeast(0))
            put("updated_at", nowIso())
        }
        writableDatabase.insertWithOnConflict("daily", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun upsertSleep(date: String, totalMin: Int, deepMin: Int, remMin: Int, lightMin: Int, awakeMin: Int) {
        val values = ContentValues().apply {
            put("date", date)
            put("total_min", totalMin.coerceAtLeast(0))
            put("deep_min", deepMin.coerceAtLeast(0))
            put("rem_min", remMin.coerceAtLeast(0))
            put("light_min", lightMin.coerceAtLeast(0))
            put("awake_min", awakeMin.coerceAtLeast(0))
            put("updated_at", nowIso())
        }
        writableDatabase.insertWithOnConflict("sleep", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun upsertHourlyHr(date: String, hour: Int, avg: Int?, min: Int?, max: Int?) {
        if (hour !in 0..23) return
        val values = ContentValues().apply {
            put("date", date)
            put("hour", hour)
            put("avg", avg)
            put("min", min)
            put("max", max)
        }
        writableDatabase.insertWithOnConflict("hr_hour", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun setMeta(key: String, value: String) {
        writableDatabase.insertWithOnConflict(
            "meta", null,
            ContentValues().apply {
                put("key", key)
                put("value", value)
            },
            SQLiteDatabase.CONFLICT_REPLACE
        )
    }

    fun meta(key: String): String? =
        readableDatabase.rawQuery("SELECT value FROM meta WHERE key = ?", arrayOf(key)).use { cursor ->
            if (cursor.moveToFirst()) cursor.getString(0) else null
        }

    fun summary(date: String): DaySummary {
        var steps = 0
        var distanceM = 0
        var calories = 0
        var activeMin = 0
        readableDatabase.rawQuery(
            "SELECT steps, distance_m, calories, active_min FROM daily WHERE date = ?", arrayOf(date)
        ).use { cursor ->
            if (cursor.moveToFirst()) {
                steps = cursor.getInt(0)
                distanceM = cursor.getInt(1)
                calories = cursor.getInt(2)
                activeMin = cursor.getInt(3)
            }
        }

        var total = 0
        var deep = 0
        var rem = 0
        var light = 0
        var awake = 0
        readableDatabase.rawQuery(
            "SELECT total_min, deep_min, rem_min, light_min, awake_min FROM sleep WHERE date = ?", arrayOf(date)
        ).use { cursor ->
            if (cursor.moveToFirst()) {
                total = cursor.getInt(0)
                deep = cursor.getInt(1)
                rem = cursor.getInt(2)
                light = cursor.getInt(3)
                awake = cursor.getInt(4)
            }
        }

        var resting: Int? = null
        var avg: Int? = null
        readableDatabase.rawQuery(
            "SELECT MIN(min), AVG(avg) FROM hr_hour WHERE date = ?", arrayOf(date)
        ).use { cursor ->
            if (cursor.moveToFirst() && !cursor.isNull(0)) {
                resting = cursor.getInt(0)
                if (!cursor.isNull(1)) avg = cursor.getInt(1)
            }
        }

        return DaySummary(date, steps, distanceM, calories, activeMin, total, deep, rem, light, awake, resting, avg)
    }

    fun hours(date: String): List<HourHr> {
        val out = ArrayList<HourHr>()
        readableDatabase.rawQuery(
            "SELECT hour, avg, min, max FROM hr_hour WHERE date = ? ORDER BY hour", arrayOf(date)
        ).use { cursor ->
            while (cursor.moveToNext()) {
                out.add(
                    HourHr(
                        hour = cursor.getInt(0),
                        avg = if (cursor.isNull(1)) null else cursor.getInt(1),
                        min = if (cursor.isNull(2)) null else cursor.getInt(2),
                        max = if (cursor.isNull(3)) null else cursor.getInt(3)
                    )
                )
            }
        }
        return out
    }

    fun range(days: Int, endDate: String): List<DaySummary> {
        val dates = dateRange(days, endDate)
        return dates.map { summary(it) }
    }

    private fun dateRange(days: Int, endDate: String): List<String> {
        val end = parseDate(endDate) ?: return emptyList()
        val out = ArrayList<String>(days)
        for (i in (days - 1) downTo 0) {
            out.add(formatDate(end - i * 86_400_000L))
        }
        return out
    }

    private fun parseDate(value: String): Long? = try {
        java.time.LocalDate.parse(value).atStartOfDay(java.time.ZoneOffset.UTC).toInstant().toEpochMilli()
    } catch (_: Exception) {
        null
    }

    private fun formatDate(epochMillis: Long): String =
        java.time.Instant.ofEpochMilli(epochMillis).atZone(java.time.ZoneOffset.UTC).toLocalDate().toString()

    private fun nowIso(): String = java.time.Instant.now().toString()

    companion object {
        private const val DB_NAME = "health.db"
        private const val DB_VERSION = 1
    }
}

data class DaySummary(
    val date: String,
    val steps: Int,
    val distanceM: Int,
    val calories: Int,
    val activeMin: Int,
    val sleepTotalMin: Int,
    val sleepDeepMin: Int,
    val sleepRemMin: Int,
    val sleepLightMin: Int,
    val sleepAwakeMin: Int,
    val restingHr: Int?,
    val avgHr: Int?
)

data class HourHr(val hour: Int, val avg: Int?, val min: Int?, val max: Int?)
