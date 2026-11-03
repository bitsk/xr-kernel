# Independent XR kernel packages

`packaging/build-debs.sh` uses the checked-in model configuration and upstream Debian packaging to build a versioned kernel image, matching modules, DTBs and headers. The ABI has an independent XR suffix. `packaging/build-uapi-deb.py` exports the three userspace contract headers without replacing distribution linux-libc-dev files.

Set ARCH, CROSS_COMPILE, XR_BUILD_DIR and JOBS for the build environment. Build inputs and archives can use SOURCE_DATE_EPOCH; Git author and commit dates remain real. Package installation does not flash device partitions. Initramfs, boot-image assembly and device acceptance are separate operations.
