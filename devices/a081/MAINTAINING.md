# Maintaining the A081 kernel patch stack

Update the pinned upstream commit, rebase the subsystem stack in prepared source, and regenerate the maintained series. Keep driver, binding and DTS changes grouped by hardware function. Validate the exported UAPI snapshot against the replayed source.

Build kernel, modules and the model DTB; check modified schemas and prepare the matching initramfs/boot image before device verification. Package installation does not flash a boot partition or promote a device baseline.
