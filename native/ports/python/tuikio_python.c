/* Tuikio's Python launcher (replaces Programs/python.c; native/recipes/python.py).
 *
 * The standard library and every Python game are a zip archive appended to this executable,
 * which lives read-only in the APK's native library directory. Python imports only from there:
 * isolated mode (no PYTHON* variables, no user site, no current directory on sys.path), no
 * `site`, and the module search path is this file alone. Nothing a game writes into its home,
 * and nothing a save archive brings in, can be imported as code.
 *
 * Usage: game_python <game id> [arguments...]: runs the module _tuikio_run, which starts the
 * game registered under that id. */
#include <Python.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static void fail(PyStatus st) {
    if (PyStatus_IsExit(st)) exit(st.exitcode);
    Py_ExitStatusException(st);
}

int main(int argc, char **argv) {
    char self[PATH_MAX];
    ssize_t n = readlink("/proc/self/exe", self, sizeof self - 1);
    if (n <= 0) { perror("game_python: /proc/self/exe"); return 70; }
    self[n] = 0;

    PyPreConfig pre;
    PyPreConfig_InitIsolatedConfig(&pre);
    pre.utf8_mode = 1;
    pre.configure_locale = 1;   /* LC_CTYPE from LANG/LC_ALL (C.UTF-8): curses needs it for UTF-8 */
    PyStatus st = Py_PreInitialize(&pre);
    if (PyStatus_Exception(st)) fail(st);

    PyConfig cfg;
    PyConfig_InitIsolatedConfig(&cfg);
    cfg.site_import = 0;
    cfg.write_bytecode = 0;
    cfg.safe_path = 1;
    cfg.install_signal_handlers = 1;
    cfg.module_search_paths_set = 1;
    wchar_t *wself = Py_DecodeLocale(self, NULL);
    if (!wself) { fputs("game_python: bad path\n", stderr); return 70; }
    st = PyWideStringList_Append(&cfg.module_search_paths, wself);
    if (PyStatus_Exception(st)) fail(st);
    st = PyConfig_SetString(&cfg, &cfg.executable, wself);
    if (PyStatus_Exception(st)) fail(st);
    st = PyConfig_SetString(&cfg, &cfg.home, L"/nonexistent");
    if (PyStatus_Exception(st)) fail(st);
    st = PyConfig_SetString(&cfg, &cfg.run_module, L"_tuikio_run");
    if (PyStatus_Exception(st)) fail(st);
    st = PyConfig_SetBytesArgv(&cfg, argc, argv);
    if (PyStatus_Exception(st)) fail(st);
    st = Py_InitializeFromConfig(&cfg);
    PyConfig_Clear(&cfg);
    PyMem_RawFree(wself);
    if (PyStatus_Exception(st)) fail(st);
    return Py_RunMain();
}
