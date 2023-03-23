export cibuildwheel_ver=2.12.1

echo """
    EXPORTING HTTP_PROXY - IF THIS SCRIPT CRASHES PRIOR TO TERMINATION THIS PROXY VALUE WILL NOT BE UNSET!
"""

export http_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 https_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 "$@"

. ../arcticdb_link/build_tooling/build_many_linux_image.sh --nobuilddocker --notmpdir

unset http_proxy