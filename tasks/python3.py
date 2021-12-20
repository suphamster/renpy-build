from renpybuild.model import task, annotator

version = "3.10.1"

@annotator
def annotate(c):
    if c.python == "3":
        c.var("pythonver", "python3.10")
        c.include("{{ install }}/include/{{ pythonver }}")


@task(kind="python", pythons="3")
def unpack(c):
    c.clean()

    c.var("version", version)
    c.run("tar xzf {{source}}/Python-{{version}}.tgz")


@task(kind="python", pythons="3", platforms="linux,mac,ios")
def patch_posix(c):
    c.var("version", version)

    c.chdir("Python-{{ version }}")
    c.patch("python3/no-multiarch.diff")
    c.patch("python3/cross-darwin.diff")

# @task(kind="python", pythons="2", platforms="ios")
# def patch_ios(c):
#     c.var("version", version)

#     c.chdir("Python-{{ version }}")
#     c.patch("ios-python2/posixmodule.patch")

#     c.run("cp {{patches}}/ios-python2/_scproxy.pyx Modules")
#     c.chdir("Modules")
#     c.run("cython _scproxy.pyx")

# @task(kind="python", pythons="2", platforms="windows")
# def patch_windows(c):
#     c.var("version", version)

#     c.chdir("Python-{{ version }}")
#     c.patchdir("mingw-w64-python2")
#     c.patch("python2-no-dllmain.diff")
#     c.patch("python2-utf8.diff")

#     c.run(""" autoreconf -vfi """)


# @task(kind="python", pythons="2", platforms="android")
# def patch_android(c):
#     c.var("version", version)

#     c.chdir("Python-{{ version }}")
#     c.patchdir("android-python2")
#     c.patch("mingw-w64-python2/0001-fix-_nt_quote_args-using-subprocess-list2cmdline.patch")
#     c.patch("python2-utf8.diff")
#     c.patch("mingw-w64-python2/0855-mingw-fix-ssl-dont-use-enum_certificates.patch")

#     c.run(""" autoreconf -vfi """)



def common(c):
    c.var("version", version)
    c.chdir("Python-{{ version }}")

    with open(c.path("config.site"), "w") as f:
        f.write("ac_cv_file__dev_ptmx=no\n")
        f.write("ac_cv_file__dev_ptc=no\n")

    c.env("CONFIG_SITE", "config.site")
    c.env("PYTHON_FOR_BUILD", "{{ host }}/bin/python3")


@task(kind="python", pythons="3", platforms="linux,mac")
def build_posix(c):

    common(c)

    c.run("""./configure {{ cross_config }} --prefix="{{ install }}" --with-system-ffi --enable-ipv6""")
    c.generate("{{ source }}/Python-{{ version }}-Setup.local", "Modules/Setup.local")
    c.run("""{{ make }}""")
    c.run("""{{ make }} install""")
    c.copy("{{ host }}/bin/python3", "{{ install }}/bin/hostpython3")

    



@task(kind="python", pythons="3", platforms="ios")
def build_ios(c):
    common(c)

    with open(c.path("config.site"), "a") as f:
        f.write("ac_cv_little_endian_double=yes\n")
        f.write("ac_cv_header_langinfo_h=no\n")
        f.write("ac_cv_func_getentropy=no\n")
        f.write("ac_cv_have_long_long_format=yes\n")

    c.run("""./configure {{ cross_config }} --prefix="{{ install }}" --with-system-ffi --disable-toolbox-glue --enable-ipv6""")
    c.generate("{{ source }}/Python-{{ version }}-Setup.local", "Modules/Setup.local")
    c.run("""{{ make }} """)
    c.run("""{{ make }} install""")
    c.copy("{{ host }}/bin/python2", "{{ install }}/bin/hostpython2")


@task(kind="python", pythons="3", platforms="android")
def build_android(c):
    common(c)

    with open(c.path("config.site"), "a") as f:
        f.write("ac_cv_little_endian_double=yes\n")
        f.write("ac_cv_header_langinfo_h=no\n")

    c.run("""./configure {{ cross_config }} --prefix="{{ install }}" --with-system-ffi --enable-ipv6""")
    c.generate("{{ source }}/Python-{{ version }}-Setup.local", "Modules/Setup.local")
    c.run("""{{ make }}""")
    c.run("""{{ make }} install""")
    c.copy("{{ host }}/bin/python3", "{{ install }}/bin/hostpython3")


@task(kind="python", pythons="3", platforms="windows")
def build_windows(c):
    common(c)

    c.env("MSYSTEM", "MINGW")
    c.env("LDFLAGS", "{{ LDFLAGS }} -static-libgcc")

    with open(c.path("config.site"), "a") as f:
        f.write("ac_cv_func_mktime=yes")

    # Force a recompile.
    with open(c.path("Modules/timemodule.c"), "a") as f:
        f.write("/* MKTIME FIX */\n")

    c.run("""./configure {{ cross_config }} --enable-shared --prefix="{{ install }}" --with-threads --with-system-ffi""")

    c.generate("{{ source }}/Python-{{ version }}-Setup.local", "Modules/Setup.local")

    with open(c.path("Lib/plat-generic/regen"), "w") as f:
        f.write("""\
#! /bin/sh
set -v
CCINSTALL=$($1 -print-search-dirs | head -1 | cut -d' ' -f2)
REGENHEADER=${CCINSTALL}/include/stddef.h
eval $PYTHON_FOR_BUILD ../../Tools/scripts/h2py.py -i "'(u_long)'" $REGENHEADER
""")

    c.run("""{{ make }}""")
    c.run("""{{ make }} install""")
    c.copy("{{ host }}/bin/python3", "{{ install }}/bin/hostpython3")


@task(kind="python", pythons="3")
def pip(c):
    c.run("{{ install }}/bin/hostpython3 -s -m ensurepip")
    c.run("{{ install }}/bin/hostpython3 -s -m pip install --upgrade future==0.18.2 six==1.12.0 rsa==3.4.2 pyasn1==0.4.2")
    c.run("{{ install }}/bin/hostpython3 -s -m pip install --upgrade urllib3==1.22 certifi idna==2.6 requests==2.20.0")
    