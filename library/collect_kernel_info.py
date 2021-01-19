#!/usr/bin/python
import glob
import re
import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

def main():
    module = AnsibleModule(
        argument_spec = dict(
            lookup_packages = dict(required=False, default=True, type='bool')
        ),
        supports_check_mode=True
    )

    # This module only performs diagnostics, so it doesn't actually change anything
    # During actual usage we return "changed" depending on booted kernel status
    if module.check_mode:
        module.exit_json(changed=False)

    params = module.params

    # Collect a list of installed kernels
    kernels = glob.glob("/lib/modules/*")

    # Identify path to the latest kernel
    latest_kernel = ""
    for kernel in kernels:
        if not latest_kernel:
            latest_kernel = kernel
            continue
        # These splits remove the path and get the base directory name, which
        # should be something like 5.4.78-1-pve, that we can compare
        right = latest_kernel.split("/")[-1]
        left = kernel.split("/")[-1]
        cmp_str = "gt"
        if subprocess.call(["dpkg", "--compare-versions", left, cmp_str, right]) == 0:
            latest_kernel = kernel

    booted_kernel = "/lib/modules/{}".format(to_text(subprocess.check_output(["uname", "-r"]).strip))

    booted_kernel_package = ""
    old_kernel_packages = []
    if params['lookup_packages']:
        for kernel in kernels:
            # Identify the currently booted kernel and unused old kernels by
            # querying which packages owns the directory in /lib/modules
            if kernel.split("/")[-1] == booted_kernel.split("/")[-1]:
                booted_kernel_package = to_text(subprocess.check_output(["dpkg-query", "-S", kernel])).split(":")[0]
            elif kernel != latest_kernel:
                old_kernel_packages.append(to_text(subprocess.check_output(["dpkg-query", "-S", kernel])).split(":")[0])

    # returns True if we're not booted into the latest kernel
    new_kernel_exists = booted_kernel.split("/")[-1] != latest_kernel.split("/")[-1]
    module.exit_json(changed=False, new_kernel_exists=new_kernel_exists, old_packages=old_kernel_packages, booted_package=booted_kernel_package)

if __name__ == '__main__':
    main()
