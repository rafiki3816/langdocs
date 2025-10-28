# Python 가상환경(venv) 사용 가이드

## 📌 가상환경이란?

가상환경(Virtual Environment)은 Python 프로젝트마다 독립적인 패키지 설치 공간을 제공하는 격리된 Python 실행 환경입니다.

```
시스템 Python
├── 프로젝트 A (venv)
│   ├── Python 3.9
│   └── 패키지 A 전용
├── 프로젝트 B (venv)
│   ├── Python 3.10
│   └── 패키지 B 전용
└── 프로젝트 C (venv)
    ├── Python 3.11
    └── 패키지 C 전용
```

---

## 🎯 가상환경을 사용해야 하는 이유

### 1. 패키지 버전 충돌 방지

#### 문제 상황
```python
# 프로젝트 A 요구사항
langchain==0.2.0
numpy==1.19.0

# 프로젝트 B 요구사항
langchain==0.3.3
numpy==1.26.0

# 시스템에 하나만 설치 가능 → 충돌 발생!
```

#### 해결 방법
```bash
# 프로젝트 A
cd project_a
python -m venv venv_a
source venv_a/bin/activate
pip install langchain==0.2.0

# 프로젝트 B
cd project_b
python -m venv venv_b
source venv_b/bin/activate
pip install langchain==0.3.3
```

### 2. 프로젝트 격리 및 의존성 관리

#### 장점
- **명확한 의존성**: 프로젝트에 필요한 패키지만 설치
- **쉬운 공유**: `requirements.txt`로 환경 재현 가능
- **깔끔한 제거**: 프로젝트 삭제 시 `venv` 폴더만 삭제

#### 실제 예시
```bash
# 현재 프로젝트의 의존성 저장
pip freeze > requirements.txt

# 다른 개발자의 환경에서
git clone <repository>
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # 동일한 환경 구성!
```

### 3. 시스템 Python 보호

#### 위험한 경우
```bash
# ❌ 시스템 Python에 직접 설치
sudo pip install some-package

# 발생 가능한 문제:
# - OS 시스템 도구 오작동
# - 권한 문제 발생
# - 패키지 업데이트 시 시스템 불안정
```

#### 안전한 방법
```bash
# ✅ 가상환경 사용
python -m venv myenv
source myenv/bin/activate
pip install some-package  # sudo 불필요!
```

### 4. Python 버전 관리

```bash
# Python 3.9로 가상환경 생성
python3.9 -m venv venv39

# Python 3.11로 가상환경 생성
python3.11 -m venv venv311

# 프로젝트별로 다른 Python 버전 사용 가능
```

### 5. 배포 환경 일치

#### 개발 환경
```bash
python -m venv venv
pip install -r requirements.txt
python app.py
```

#### Docker 배포
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN python -m venv venv
RUN ./venv/bin/pip install -r requirements.txt
COPY . .
CMD ["./venv/bin/python", "app.py"]
```

#### 클라우드 배포 (AWS Lambda 예시)
```bash
# 가상환경에서 패키지 설치
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -t ./package
# package 폴더를 Lambda로 배포
```

---

## 🛠️ 가상환경 사용법

### 기본 명령어

#### 1. 생성
```bash
# 기본 방법
python -m venv venv

# 특정 Python 버전 지정
python3.10 -m venv venv

# 시스템 패키지 포함 (권장하지 않음)
python -m venv venv --system-site-packages
```

#### 2. 활성화
```bash
# macOS/Linux
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# 활성화 확인
which python  # venv 내부 python 경로 표시
```

#### 3. 비활성화
```bash
deactivate
```

#### 4. 삭제
```bash
# 가상환경 삭제 (폴더 삭제)
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows
```

### 프로젝트별 설정 예시

#### LangChain 챗봇 프로젝트
```bash
# 1. 프로젝트 폴더 생성
mkdir langchain-chatbot
cd langchain-chatbot

# 2. 가상환경 생성
python -m venv venv

# 3. 활성화
source venv/bin/activate

# 4. 필요 패키지 설치
pip install langchain langchain-upstage chromadb

# 5. 개발 시작
python main.py

# 6. 작업 종료
deactivate
```

---

## 📋 모범 사례 (Best Practices)

### 1. `.gitignore`에 추가
```gitignore
# 가상환경 폴더는 git에 올리지 않음
venv/
env/
.venv/
ENV/

# 대신 requirements.txt만 공유
# requirements.txt는 반드시 포함!
```

### 2. 가상환경 이름 규칙
```bash
venv        # 일반적인 이름
.venv       # 숨김 폴더로 생성
env         # 짧은 이름
<project>-env  # 프로젝트별 구분
```

### 3. requirements.txt 관리
```bash
# 개발용과 프로덕션용 분리
requirements.txt       # 프로덕션 의존성
requirements-dev.txt   # 개발 도구 포함

# 버전 고정
langchain==0.3.3      # 특정 버전
langchain>=0.3.0      # 최소 버전
langchain~=0.3.0      # 호환 버전 (0.3.x)
```

### 4. 자동 활성화 스크립트
```bash
# .envrc 파일 (direnv 사용 시)
source venv/bin/activate

# VS Code settings.json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true
}
```

---

## 🔍 문제 해결

### 1. 권한 오류
```bash
# 문제
pip install: Permission denied

# 해결
# 가상환경 활성화 확인
which pip  # venv/bin/pip 경로여야 함
```

### 2. 잘못된 Python 버전
```bash
# 문제
python -m venv venv
# Python 2.7로 생성됨

# 해결
python3 -m venv venv
# 또는
python3.10 -m venv venv
```

### 3. 가상환경 재생성
```bash
# 패키지 목록 저장
pip freeze > requirements.txt

# 가상환경 삭제
deactivate
rm -rf venv

# 새로 생성
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 💡 고급 팁

### 1. 가상환경 위치 확인
```python
import sys
print(sys.prefix)  # 가상환경 경로
print(sys.executable)  # Python 실행 파일 경로
```

### 2. 여러 프로젝트 동시 작업
```bash
# tmux 또는 여러 터미널 사용
# 터미널 1
cd project1
source venv/bin/activate

# 터미널 2
cd project2
source venv/bin/activate
```

### 3. 가상환경 백업
```bash
# requirements.txt로 백업
pip freeze > requirements.txt

# 전체 환경 정보 포함
pip list --format=freeze > requirements-full.txt
```

---

## 📊 가상환경 vs 다른 도구들

| 도구 | 장점 | 단점 | 사용 시기 |
|------|------|------|-----------|
| **venv** | Python 내장, 간단함 | Python 버전 관리 불가 | 단일 프로젝트 |
| **virtualenv** | Python 2 지원, 더 많은 기능 | 별도 설치 필요 | 레거시 프로젝트 |
| **conda** | 패키지 + Python 버전 관리 | 무겁고 복잡함 | 데이터 과학 프로젝트 |
| **pipenv** | Pipfile로 의존성 관리 | 느림, 학습 곡선 | 의존성 잠금 필요 시 |
| **poetry** | 현대적 의존성 관리 | 학습 곡선 | 패키지 배포 시 |
| **pyenv** | Python 버전 관리 | venv와 별도 사용 | 여러 Python 버전 필요 시 |

---

## 🎓 결론

가상환경은 Python 개발의 **필수 도구**입니다:

1. ✅ **프로젝트 격리**: 각 프로젝트가 독립적인 환경 유지
2. ✅ **버전 관리**: 패키지 버전 충돌 방지
3. ✅ **협업 용이**: requirements.txt로 환경 공유
4. ✅ **배포 준비**: 프로덕션 환경과 동일한 설정
5. ✅ **시스템 보호**: 시스템 Python 영향 없음

**"One Project, One Virtual Environment"** - 이것이 Python 개발의 황금률입니다!

---

## 📚 참고 자료

- [Python 공식 venv 문서](https://docs.python.org/3/library/venv.html)
- [Real Python - Virtual Environments](https://realpython.com/python-virtual-environments-a-primer/)
- [pip 사용자 가이드](https://pip.pypa.io/en/stable/user_guide/)
- [Python Packaging User Guide](https://packaging.python.org/guides/)

---

**작성일**: 2024-10-28
**버전**: 1.0.0
**프로젝트**: LangChain Documentation Chatbot