# A081 kernel configuration

The model kernel configuration is maintained in config/kernel.config. Functional changes are maintained only in the top-level patches/series. Use tools/prepare-source.py and packaging/build-debs.sh for reproducible source preparation and package builds.

Userspace board policy, thermal services, firmware locks and rootfs integration belong to the independent integration repository. Historical source archives and validated device baselines remain separate.
