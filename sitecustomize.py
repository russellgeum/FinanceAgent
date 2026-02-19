"""프로젝트 전역 Python 바이트코드 생성을 비활성화한다."""

from __future__ import annotations

import os
import sys


os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
