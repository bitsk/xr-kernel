# Independent XR kernel packages

`packaging/build-debs.sh` uses the checked-in model configuration and upstream Debian packaging to build a versioned kernel image, matching modules, DTBs and headers. The ABI has an independent XR suffix. `packaging/build-uapi-deb.py` exports the three userspace contract headers without replacing distribution linux-libc-dev files.

Set ARCH, CROSS_COMPILE, XR_BUILD_DIR and JOBS for the build environment. Build inputs and archives can use SOURCE_DATE_EPOCH; Git author and commit dates remain real. Package installation does not flash device partitions. Initramfs, boot-image assembly and device acceptance are separate operations.

Select `--device vr700` on `build-debs.sh` or `tools/prepare-source.py`, or set
`XR_KERNEL_DEVICE=vr700`; omission keeps the A081 lock. Preparation copies the
selected commit, config and fragment list into `packaging/source-lock.json`.
`build-in-source.sh` uses that receipt and rejects a different requested device
or source commit. VR700's initial config has no A081 camera/scheduling fragments.
The A081-specific `kernel-candidate.py` is not a VR700 boot-image builder.
