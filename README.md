# GameAssetAI

GameAssetAI는 Codex Desktop 또는 VS Code + Codex에서 사용하는 스타일 기반 게임 에셋 제작
Skill 시스템입니다. Blender 중심의 3D 제작·수정과 선택적인 Rig/Animation, 2D·픽셀·스프라이트
출력을 하나의 게임별 Profile 아래에서 운영하도록 설계되어 있습니다.

현재 Repository는 제품 기반 단계입니다. 카탈로그, Asset Specification, Workspace/Profile,
개발 실험 및 사용자 결과 경로, 네 개의 설치형 Skill 패키징이 동작합니다. 범용 텍스트→3D,
모든 생물 생성, 자유형 메시 수정, 네 가지 3D 스타일의 자동 생성, 완전한 8방향 제작은 아직
완료되지 않았습니다. 정확한 경계는 [Capabilities](docs/capabilities.md)를 확인하십시오.

## 구조

```text
catalog/                 에셋·스타일·Provider 데이터
src/gameassetai/         공통 Runtime과 제한된 Blender helper
skills/                  작업 중심 제품 Skill 4개
packaging/               설치형 bundle entrypoint
workspace-template/      사용자 Workspace 템플릿
blender_addon/           선택적인 Blender UI/실행 계층
scripts/                 개발 checkout 명령
tests/                   격리된 offline 검증
docs/                    현재 제품·기술 기준
output/                  선택적인 로컬 개발 실험 결과(미추적, 필요할 때만 생성)
```

Repository, 설치된 Skill, 사용자 Workspace, 외부 게임 프로젝트, 결과물은 서로 다른 소유
영역입니다. 기존 Blender·Unity 프로젝트를 Workspace 안으로 옮길 필요가 없습니다.

## 최초 설치

1. 프로젝트 범위 사용자는 승인된 `master`에서 GitHub Actions가 생성한 단일
   `dist/workspace` 브랜치를 원하는 Workspace 경로로 Clone합니다. Draft PR만으로 이
   배포 브랜치가 생성되거나 갱신되지는 않습니다.

   ```powershell
   git clone --branch dist/workspace --single-branch `
     https://github.com/jiwoo7158/GameAssetAI.git <workspace>
   python -B <workspace>\.agents\skills\gameassetai-workspace\scripts\gameassetai.py `
     workspace init-clone <workspace>
   ```

   초기화는 배포 메타데이터와 네 Skill을 먼저 검증하고, Git에서 무시되는 개인
   `config/`와 `profiles/`만 안전하게 추가합니다. 재실행해도 기존 개인 파일을 덮어쓰지
   않습니다.

2. 사용자 범위 사용자는 같은 배포본의 `.agents/skills/` 아래 네 디렉터리만
   `$HOME/.agents/skills/`로 복사하고, 별도 경로에 Workspace를 생성합니다. 프로젝트와
   사용자 범위에 같은 Skill을 중복 설치하면 두 항목이 표시될 수 있으므로 한 범위를
   선택합니다. 기존 `.codex/skills` 설치는 자동 이동·삭제하지 않습니다.

   현재 공식 경로와 탐색 규칙은
   [OpenAI Build skills 문서](https://developers.openai.com/codex/skills/)를 참고하십시오.
   파일 검증은 실제 Codex Desktop/VS Code 인식을 증명하지 않으므로 `/skills` 또는
   `$gameassetai-workspace`로 별도 확인합니다.

3. 개발자는 필요하면 기존 bundle 명령으로 독립 Skill을 빌드·검증할 수 있습니다.

   ```powershell
   python -B scripts/gameassetai.py package build . <bundle>
   python -B scripts/gameassetai.py package validate <bundle>
   ```

   bundle 기반 프로젝트 설치도 Workspace를 먼저 검증한 뒤 `.agents/skills`를 생성합니다.

4. 설치 뒤 게임 Profile을 생성하고 선택합니다.

   ```powershell
   python -B scripts/gameassetai.py profile create <workspace> my-game `
     --name "My Game" --description "Persistent game art profile" `
     --three-d-style stylized-chibi-low-poly
   python -B scripts/gameassetai.py profile select <workspace> my-game
   python -B scripts/gameassetai.py workspace validate <workspace> --require-profile
   ```

   공식 `styles.three_d`와 `styles.two_d`에는 카탈로그의 올바른 차원 ID만 저장됩니다.
   사용자 고유의 자유로운 스타일 설명은 `art_direction` 규칙으로 관리합니다.

5. Blender와 Blender MCP 연결은 별도로 확인합니다. Skill 설치는 Blender, MCP, 외부 AI,
   UnityWorkbench를 자동 설치하거나 설정하지 않습니다.

## 일상적인 사용자 작업

1. Codex Desktop 또는 VS Code + Codex에서 GameAssetAI-Workspace를 엽니다.
2. 활성 Profile과 지속적인 스타일 규칙을 확인합니다.
3. 텍스트, 공식 스타일 프리셋, 사용자가 준비한 역할별 참고 이미지를 제공합니다.
4. 생성·수정 요청과 시각적 검토를 진행합니다.
5. 공통 Runtime으로 결과 경로를 할당합니다.

   ```powershell
   python -B scripts/gameassetai.py outputs begin <workspace> --space workspace `
     --category equipment-prop --asset bronze-sword --purpose initial-model
   ```

   기본은 Workspace `outputs/`이며, 사용자가 명시한 기존 외부 디렉터리는
   `--output-root`로 한 작업에만 사용할 수 있습니다. 우선순위는 일회성 경로, Profile
   `output_defaults.root`, Workspace 공통 설정, 내부 `outputs/` 순서입니다.

   결과는 다음 구조에 저장됩니다.

   ```text
   outputs/<active-game>/<category>/<asset-id>/<number>-<purpose>/
   ```

   카테고리는 `character`, `equipment-prop`, `environment`, `vfx-mesh` 중 하나입니다. 같은
   에셋의 수정 결과는 같은 에셋 ID에서 다음 번호를 사용합니다. 진행 중 작업을 계속하려면
   정확한 작업 경로를 `outputs continue`로 검증합니다. 날짜·UUID 이름이나 전역 카운터는
   사용하지 않습니다.

   실제 파일은 필요한 `models/`, `previews/`, `sprites/`, `exports/` 경로만 Runtime으로
   예약한 뒤 생성·등록합니다. 등록은 해당 예약을 소비하며, 미해결 예약이 있으면 작업
   상태를 변경하지 않습니다. `complete`는 제작 종료일 뿐 품질 승인이 아니며,
   `accepted`/`rejected`는 등록된 결과물과 실제 시각·의미 검토 기록이 필요합니다.

`outputs/`의 일부나 전체를 이동·삭제해도 Profile, 설치된 Skill, 카탈로그, 새 독립 작업에는
영향이 없습니다. 삭제된 특정 작업을 계속할 수는 없으며 시스템은 이를 자동 복원하지 않습니다.
외부 출력 루트 자체가 이동·삭제되면 이전 위치를 다시 만들지 않고 새 경로를 선택하거나 설정을
해제합니다.

## 개발 실험

개발 실험은 사용자 Workspace와 분리하여 다음 구조를 사용합니다.

```text
output/experiments/<experiment-id>/<category>/<asset-id>/<number>-<purpose>/
```

실험 ID는 에셋 이름이 아니라 검증 목표를 나타냅니다. 기존 `experiment.json`의 목적·핵심
질문·평가 기준이 같을 때만 명시적으로 재사용하고, 다른 검증 목표는 새 실험으로 분리합니다.
새 요청마다 실험을 만들거나 같은 에셋이라는 이유로 다른 목표를 합치지 않습니다.

```powershell
python -B scripts/gameassetai.py outputs experiment list .
python -B scripts/gameassetai.py outputs experiment create . chibi-character-quality `
  --purpose "Validate chibi visual quality" `
  --question "Does the method meet the target silhouette?" `
  --criterion "Readable front and three-quarter silhouette"
python -B scripts/gameassetai.py outputs begin . --space development `
  --experiment chibi-character-quality --category character `
  --asset chibi-adventurer --purpose initial-model
```

`/output/`은 Git에 포함되지 않으며 없어도 됩니다. 일반 Unit/통합 테스트는 운영체제 임시
디렉터리만 사용합니다.

## 개발 검증

```powershell
python -B scripts/validate_repo.py
python -B -m unittest discover -s tests -p "test_*.py" -v
```

GitHub Actions는 Linux와 Windows에서 같은 offline 기반 검증을 실행합니다. 이 검증은 실제
Blender 시각 검수, MCP 실행, Codex 호스트 인식 또는 Unity round trip을 증명하지 않습니다.

## 문서

- [Product definition](docs/product-definition.md)
- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Capabilities](docs/capabilities.md)
- [Workspace](docs/workspace.md)
- [Distribution](docs/distribution.md)
- [Quality and testing](docs/quality.md)
- [Roadmap](docs/roadmap.md)
