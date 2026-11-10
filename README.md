# GameAssetAI

GameAssetAI는 Codex Desktop 또는 VS Code + Codex에서 설치하여 사용하는 스타일 기반 게임
에셋 제작 기반입니다. Blender를 중심으로 신규 제작, 기존 에셋 수정, Rig/Animation 작업,
3D/2D 출력 과정을 연결하며, 생성 기술은 교체 가능한 provider로 분리합니다.

현재 릴리스는 **제품 기반 단계**입니다. 카탈로그, 스타일 명세, Asset Specification,
Workspace/Profile, 결과물 run, 설치형 Skill 패키징은 동작합니다. 범용 prompt-to-3D,
네 가지 3D 스타일의 자동 생성, 비인간형 생성, 자유형 의미 수정, 완전한 8방향 제작은 아직
지원 완료가 아닙니다. 정확한 상태는 [capabilities](docs/capabilities.md)를 기준으로 합니다.

## 구조

```text
catalog/                 asset type, style, generation-provider data
src/gameassetai/         shared product runtime and retained Blender helpers
skills/                  four task-oriented source Skills
packaging/               generated bundle entrypoint
workspace-template/      safe persistent user Workspace template
blender_addon/           retained Blender-native UI/execution layer
scripts/                 development checkout entrypoints
tests/                   focused offline product and retained-contract tests
docs/                    current product and engineering authority
```

Repository는 개발·배포 원본이고, 설치된 Skill은 실행 사본이며, Workspace는 사용자 설정과
결과물을 보관하는 별도 공간입니다. 기존 Unity/Blender 프로젝트는 Workspace 안으로 옮기지
않습니다.

## 개발 checkout에서 확인

Python 3.10+ 표준 라이브러리만으로 기반 기능을 검사할 수 있습니다.

```powershell
python -B scripts/gameassetai.py catalog validate --root catalog
python -B scripts/gameassetai.py workspace create D:\AI\GameAssetAI-Workspace --template workspace-template
python -B scripts/gameassetai.py profile create D:\AI\GameAssetAI-Workspace my-game --name "My Game" --description "Persistent game art profile"
python -B scripts/gameassetai.py profile select D:\AI\GameAssetAI-Workspace my-game
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B scripts/validate_repo.py
```

실제 개인 Workspace 대신 임시 경로에서 먼저 시험하십시오. `workspace create`는 이미 유효한
Workspace를 변경 없이 연결하고, 인식된 구형 Workspace는 migration 필요 상태로 보고할 뿐
자동 덮어쓰지 않습니다. 과거의 파괴적인 `--force` 동작은 제거되었습니다.

## Skill bundle 만들기와 설치

```powershell
python -B scripts/gameassetai.py package build . .local\gameassetai-skill-bundle
python -B scripts/gameassetai.py package validate .local\gameassetai-skill-bundle
python -B scripts/gameassetai.py package install .local\gameassetai-skill-bundle D:\AI\GameAssetAI-Workspace\.agents\skills
```

생성된 네 Skill은 각각 공유 runtime, catalog, Workspace template을 포함하므로 개발 Repository
절대 경로가 필요하지 않습니다. 기존 설치 갱신은 명시적인 새 backup 경로를 요구하며 이전
설치를 보존합니다. 자세한 내용은 [distribution](docs/distribution.md)을 참조하십시오.

## Blender

Blender MCP 설치·설정은 외부 사용자 환경입니다. GameAssetAI 설치가 이를 자동 변경하지
않습니다. `blender_addon/`은 보존된 UI/실행 계층이지만 현재 주로 2D preview/output 보조에
한정됩니다. 실제 Blender 기능을 사용할 때는 현재 Scene과 MCP 기능을 먼저 확인하십시오.

## 제품 문서

- [Product definition](docs/product-definition.md)
- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Capabilities](docs/capabilities.md)
- [Workspace](docs/workspace.md)
- [Distribution](docs/distribution.md)
- [Quality and testing](docs/quality.md)
- [Roadmap](docs/roadmap.md)
