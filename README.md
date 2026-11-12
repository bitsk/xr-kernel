# xr-kernel

MIX openKylin 的内核来源锁定、UAPI 导出和 Debian 构建封装。

驱动、binding/DTS 和内核配置只在 [bitsk/qiyu-kernel](https://github.com/bitsk/qiyu-kernel) 维护。本仓库通过 upstream.json 选择已验证提交，准备真实 Git 历史，并校验导出的 UAPI；不再维护另一套驱动补丁。旧补丁栈仍保留在 Git 历史中。

`tools/prepare-source.py --output NEW_SOURCE` 准备固定源码；可用 `--upstream-repo` 提供同一上游的 Git 对象缓存。`packaging/build-debs.sh` 只接受锁定的源码提交，构建内核、模块与独立 UAPI 包。配置及可选相机、PD、调度片段来自唯一内核源码仓库。

构建不刷写设备、不变更启动选择，也不代表新的实机验收。型号用户态、固件安装、温控服务与 rootfs 配方归 openkylin-xr-integration 和 xr-image-tools。
