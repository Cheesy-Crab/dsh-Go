package io.github.ccch1mneyyy.dsh_app.health

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.net.Uri

/**
 * 自动启动钩子（fork 新增）。
 *
 * Android 会在 Application.onCreate 之前创建所有已声明的 ContentProvider，
 * 于是可以用它来初始化健康模块，而**不必修改上游的 Application / MainActivity**。
 *
 * 只做初始化，不对外提供任何数据（exported=false）。
 */
class HealthBootstrapProvider : ContentProvider() {

    override fun onCreate(): Boolean {
        context?.let { HealthRuntime.ensureStarted(it) }
        return true
    }

    override fun query(
        uri: Uri,
        projection: Array<out String>?,
        selection: String?,
        selectionArgs: Array<out String>?,
        sortOrder: String?
    ): Cursor? = null

    override fun getType(uri: Uri): String? = null

    override fun insert(uri: Uri, values: ContentValues?): Uri? = null

    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = 0

    override fun update(
        uri: Uri,
        values: ContentValues?,
        selection: String?,
        selectionArgs: Array<out String>?
    ): Int = 0
}
