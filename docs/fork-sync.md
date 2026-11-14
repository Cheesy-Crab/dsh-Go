# Fork 同步上游：rebase 方案

我们维护 `Cheesy-Crab/dsh-Go`（fork）来加定制，上游 `ccch1mneyyy/dsh-Go` 迭代很快（平均每天十几笔提交）。
本文记录**怎么在保留定制的前提下随时同步上游**，以及踩过的坑。

## 一、当前状态

| 项 | 值 |
|---|---|
| 最近一次同步 | 上游 `719fed0`（2026-11-14） |
| 我们领先上游 | **15 笔提交** |
| 我们的改动文件 | **10 个**（7 新增 + 3 修改） |
| 最近一次 rebase 结果 | ✅ 15/15 干净应用，**零冲突** |

### 我们的 delta（改过的上游文件）

```
A .github/workflows/attach-update-manifest.yml
A .github/workflows/build-apk-full.yml
A .github/workflows/build-apk.yml
A .github/workflows/verify-release.yml
A docs/health-architecture.png
A docs/health-integration.md
A docs/shizuku-self-update.md
M app/lib/update/update_config.dart     ← updateRepo 指向本 fork（1 行）
M app/pubspec.yaml                       ← 版本号（1 行）
M runtime/build-runtime.sh               ← proot pin（3 行）
```

新增文件永不冲突；冲突面只有那 3 个修改文件、5 行代码。

## 二、一次性准备

```bash
# 加只读上游
git remote add upstream https://github.com/ccch1mneyyy/dsh-Go.git

# 记住冲突解法，下次自动应用
git config rerere.enabled true

# 确认历史完整（浅克隆必须处理，见第四节）
git rev-list --count HEAD   # 太小说明是浅克隆
```

## 三、每次同步的命令

```bash
git fetch upstream main
git switch main

# 历史完整时：
git rebase upstream/main

# 浅克隆 / 不确定基底时（显式指定范围，只重放我们的提交）：
git rebase --onto upstream/main <上次同步的上游提交> main

git push origin main --force-with-lease
```

### 为什么需要 `--onto`

`git rebase upstream/main` 重放的是 **合并基点之后的所有提交**。
如果 merge-base 算错（浅克隆常见），它会把上游自己的历史也重放一遍，变成几百个提交互相打架。

`--onto upstream/main <base> main` 明确告诉 git：**只把这个范围内的提交搬到上游最新之上**。

上次用的 base 就是 fork 点 `f07a98c`（上游当时的 tip）。

## 四、浅克隆的坑（重要）

我们的工作目录是 `--depth 1` 拉的，历史被截断，`git merge-base` 会算错：

```
git merge-base upstream/main main
→ ca3c420     # 实际 fork 点是 f07a98c
```

后果：
1. `git rebase upstream/main` 行为不可预测
2. 部分克隆（`--filter=blob`）在 rebase 时要按需回源拉 blob，网络一抖就失败

### 处理方式

**推荐：同步放在一个完整历史的克隆里做**

```bash
git clone --filter=blob:none --no-checkout \
  https://github.com/Cheesy-Crab/dsh-Go.git dsh-go-sync
cd dsh-go-sync
git remote add upstream https://github.com/ccch1mneyyy/dsh-Go.git
```

只有历史、不落大文件；rebase 需要 blob 时再按需取。

**或者：把当前克隆加深**

```bash
git fetch --unshallow --filter=blob:none
```

## 五、错误与修复

| 现象 | 原因 | 处理 |
|---|---|---|
| `SSL_ERROR_SYSCALL` / `could not fetch ... from promisor remote` | 部分克隆回源时网络抖动 | 重试；或改用完整克隆 |
| `no merge base` | 浅克隆太浅 | `git fetch --deepen=400` 或 `--unshallow` |
| rebase 后提交数暴涨 | 用了 `git rebase upstream/main` 而 merge-base 不对 | 用 `--onto` 限定范围 |
| 冲突出现在 `pubspec.yaml` | 上游改了版本号 | 保留我们的版本；或改用 `fork/version.txt`（见第六节） |

## 六、后续可做的三个减冲突改造（未做）

1. **版本号移出 `pubspec.yaml`**
   上游每次发版都会改这个文件。改成 `fork/version.txt`，CI 构建时用
   `--build-name=$(cat fork/version.txt)` 传入。

2. **proot pin 移出 `runtime/build-runtime.sh`**
   上游高频改 pin。改成 `fork/runtime-pins.env`，脚本里加一行 `source`。

3. **一键同步脚本 `tools/sync-upstream.sh`**
   把「fetch → rebase → 校验 delta → 提示构建」打包成一条命令。

## 七、同步后校验清单

```bash
# 1. 我们的提交数没变
git rev-list --count upstream/main..main        # 应为 15

# 2. delta 文件还是那 10 个
git diff --name-status upstream/main main

# 3. 关键改动还在
git grep -n "updateRepo = 'Cheesy-Crab/dsh-Go'" -- app/lib/update/update_config.dart
git grep -n "PROOT_VERSION" -- runtime/build-runtime.sh

# 4. 推送后看 CI
#    Build APK (slim) 应当成功
```

## 八、给以后接手的人

- **不要在浅克隆里做同步**，至少先 `--deepen` 或 `--unshallow`
- **每次同步都对比第七节的清单**，确保定制没被上游覆盖
- 上游改了更新模块（`dl.dshtui.com` 优先），我们用 `--dart-define` 关掉了，
  如果上游改了这些 define 的名字，构建会退回上游行为，记得检查
