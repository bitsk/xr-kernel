# xr-kernel

openKylin XR 的按设备内核来源锁定、UAPI 导出和 Debian 构建封装。

驱动、binding/DTS 和内核配置只在 [bitsk/qiyu-kernel](https://github.com/bitsk/qiyu-kernel) 维护。本仓库通过来源锁选择准确提交，准备真实 Git 历史，并校验导出的 UAPI；不再维护另一套驱动补丁。旧补丁栈仍保留在 Git 历史中。

`tools/prepare-source.py --output NEW_SOURCE` 准备固定源码；可用 `--upstream-repo` 提供同一上游的 Git 对象缓存。`packaging/build-debs.sh` 只接受锁定的源码提交，构建内核、模块与独立 UAPI 包。配置及可选相机、PD、调度片段来自唯一内核源码仓库。

默认设备仍是 `a081`，使用原有 `upstream.json`。显式选择 `--device vr700` 或 `XR_KERNEL_DEVICE=vr700` 时，使用 `devices/vr700/upstream.json`。准备目录内的 `packaging/source-lock.json` 保存本次选择；包构建读取其中的提交、配置和片段，VR700 不合入 A081 相机或调度片段。

从仓库目录构建 VR700 / DREAM Pro 软件包：

```sh
XR_SOURCE_DIR=/tmp/xr-vr700-source \
XR_BUILD_DIR=/tmp/xr-vr700-build \
JOBS=4 packaging/build-debs.sh --device vr700
```

`XR_SOURCE_DIR` 必须是源码工作区之外的新目录；若使用尚未发布的本地内核提交，额外设置 `XR_UPSTREAM_REPO` 指向包含锁定提交的 `qiyu-kernel` 检出。仅准备源码可使用 `tools/prepare-source.py --device vr700 --output NEW_SOURCE`。

VR700 是独立板级候选，已包含 CPU/GPU、双 DSI、UFS、USB2 外设、按键、风扇、SLPI/CDSP、四路 OV7251 和手柄 UART。当前能力候选另外接入 QCA6390、电量/充电、5V Type-C sink、Venus 和 ADSP，并提供调度/性能采样接口及 FastRPC 重启资源生命周期修复。音频声卡/功放路由与本机无线板级固件仍需独立验证；VR700 无彩透硬件。不得继承 A081 固件与私有标定。构建不代表实机功能或佩戴验收；VR700 镜像使用 `packaging/build-recovery.py` 的显式输入，`packaging/kernel-candidate.py` 仍只适用于既有 A081 基线。

构建不刷写设备、不变更启动选择，也不代表新的实机验收。型号用户态、固件安装、温控服务与 rootfs 配方归 openkylin-xr-integration 和 xr-image-tools。

当前 VR700 锁选择 `core-repair` 诊断版本，和默认版本消费同一份板级 DTS；仅通过模块加载控制隔离探测。FastRPC 等待代、DSP/媒体启动和电源逐项探测已取得实机记录；无线正在分步验证，不能视为完整功能验收。供电范围保留本型号原厂约束，未采用无合法档位的名义 CNSS 固定请求。
