"""
Minimal fake `streamlit` module, used only to execute app.py/pages/*.py logic
and catch real bugs (wrong column names, type errors, broken pandas calls)
without Streamlit actually being installed in this environment. This is NOT
a replacement for running the real app locally — it doesn't check that
anything renders correctly, only that the Python underneath it doesn't crash.
Delete this file before deploying; it's a dev-time check only, not part of
the app itself.
"""
import sys
import types


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Col:
    def metric(self, *a, **k):
        assert isinstance(a[0], str)

    def caption(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _noop(*a, **k):
    return None


def _columns(spec):
    n = spec if isinstance(spec, int) else len(spec)
    return [_Col() for _ in range(n)]


def _expander(*a, **k):
    return _Ctx()


fake_st = types.ModuleType("streamlit")
fake_st.set_page_config = _noop
fake_st.title = _noop
fake_st.caption = _noop
fake_st.subheader = _noop
fake_st.markdown = _noop
fake_st.metric = lambda *a, **k: (_ for _ in ()).throw(AssertionError("bad metric call")) if not a else None
fake_st.columns = _columns
fake_st.line_chart = lambda data, **k: (_ for _ in ()).throw(AssertionError("line_chart got no data")) if data is None or len(data) == 0 else None
fake_st.bar_chart = fake_st.line_chart
fake_st.dataframe = lambda data, **k: (_ for _ in ()).throw(AssertionError("dataframe got no data")) if data is None else None
fake_st.table = _noop
fake_st.expander = _expander
fake_st.checkbox = lambda *a, **k: False
fake_st.info = _noop
fake_st.warning = _noop
fake_st.error = _noop
fake_st.sidebar = types.SimpleNamespace(markdown=_noop)

sys.modules["streamlit"] = fake_st

import runpy  # noqa: E402

for f in [
    "app.py",
    "pages/1_🔥_12_Hour_Wait_Crisis.py",
    "pages/2_🏥_Trust_Comparison.py",
    "pages/3_🔮_Winter_Forecast.py",
]:
    print(f"--- Running {f} ---")
    runpy.run_path(f, run_name="__main__")
    print(f"--- {f} OK ---\n")

print("All pages executed without error against the fake streamlit stub.")
