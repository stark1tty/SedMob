"""Property-based tests for profile photo functionality."""
import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
from sedmob.app import create_app
from sedmob.models import db as _db

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    """Replicate the allowed_file helper defined inside create_app() for direct testing."""
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test",
        "WTF_CSRF_ENABLED": False,
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    with app.app_context():
        yield _db


# Feature: profile-photos, Property 1: Extension validation
# **Validates: Requirements 1.4, 3.1**
@given(
    base=st.text(min_size=0, max_size=50),
    ext=st.sampled_from(
        list(ALLOWED_EXTENSIONS) + ["bmp", "tiff", "pdf", "exe", "txt", "svg"]
    ),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allowed_file_iff_extension_in_set(base, ext):
    """For any filename with a dot and extension, allowed_file returns True iff
    the lowercased extension is in the allowed set {"png", "jpg", "jpeg", "gif", "webp"}."""
    filename = f"{base}.{ext}"
    expected = ext.lower() in ALLOWED_EXTENSIONS
    assert allowed_file(filename) == expected


@given(name=st.text(min_size=1, max_size=50).filter(lambda s: "." not in s))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allowed_file_rejects_no_extension(name):
    """Filenames without a dot are always rejected by allowed_file."""
    assert allowed_file(name) is False
