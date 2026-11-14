# 用 Shizuku 做免拦截的自更新（小米等机型）

系统安装器会扫描 APK，把内置 Linux 运行时的包判成 `Spyware:a/FakeApp.hideX_FeedAidlc`。
更新弹窗里的「安装路线」可以绕过它：Shizuku 或本机 ADB 直接调 PackageInstaller，
不经过系统安装器界面，所以扫描没有机会介入。

## 三条路线

| 路线 | 行为 | 过小米扫描 |
|---|---|---|
| 正常安装（默认） | 打开系统安装器 | ❌ 会弹风险提示 |
| Shizuku / Sui | UserService 以 shell 身份静默安装 | ✅ |
| 本机 ADB | 用已配对的无线调试身份执行安装 | ✅ |

## 配置步骤（纯手机，Android 11+）

1. 安装 **Shizuku**（`moe.shizuku.privileged.api`；App 也识别 Sui）
2. 设置 → 我的设备 → 全部参数 → 连点系统版本 7 次，打开开发者选项
3. 开发者选项 → 打开「无线调试」→ 进入无线调试 → 使用配对码配对
4. Shizuku → 「通过无线调试启动」→ 输入配对码
5. DSH Go → 更新弹窗 → 安装路线选 **Shizuku** → 授权 → 系统弹窗允许

之后更新点一下即可静默安装。若选「本机 ADB」，走同一套无线调试配对，
入口在更新弹窗的「打开 Android Shell 配对引导」。

## 四个坑

1. **重启后 Shizuku 停止**：无线调试启动是临时的，重启要重新配对启动；
   永久生效需要 root 或 Sui (Magisk)。
2. **MIUI/HyperOS 会杀后台**：给 Shizuku 开「自启动」，电池策略设为「无限制」。
3. **本机 ADB 也要先配对**：配对码和端口 App 不保存、不写日志。
4. **签名必须一致**：v1.0.16-fork.1 是 debug 签名，与 v1.0.17（新密钥）不同，
   首次必须卸载重装；之后才能用 Shizuku 无感升级。

## 源码位置

- `android/app/src/main/kotlin/.../update/privileged/SelfUpdateShizuku.kt` — 连接、鉴权、安装
- `android/app/src/main/kotlin/.../update/privileged/PrivilegedSelfUpdater.kt` — 校验与状态机
- `lib/ui/update/update_sheet.dart` — 安装路线 UI
- `lib/update/privileged_installer.dart` — MethodChannel 封装
