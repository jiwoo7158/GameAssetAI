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

1. 개발 checkout에서 bundle을 만들고 검증합니다.

   ```powershell
   python -B scripts/gameassetai.py package build . <bundle>
   python -B scripts/gameassetai.py package validate <bundle>
   ```

2. Workspace를 Codex 프로젝트로 사용할 경우에는 반드시 Workspace 생성/연결·검증을 먼저
   하고 네 Skill을 설치합니다. 통합 명령이 이 순서를 보장합니다.

   ```powershell
   python -B scripts/gameassetai.py package install-project <bundle> <workspace> `
     --template workspace-template
   python -B scripts/gameassetai.py package validate-install <workspace>\.codex\skills
   ```

   새 폴더에 `.codex/skills`부터 만들면 미등록 비어 있지 않은 Workspace가 될 수 있으므로
   프로젝트 범위에서는 일반 `package install`을 먼저 실행하지 않습니다.

   사용자 전역 범위는 Workspace보다 먼저 설치할 수 있습니다.

   ```powershell
   python -B scripts/gameassetai.py package install <bundle> `
     $env:USERPROFILE\.codex\skills
   python -B scripts/gameassetai.py package validate-install `
     $env:USERPROFILE\.codex\skills
   ```

   OpenAI 공식 예시의 Codex 경로는 프로젝트 `.codex/skills/<name>/SKILL.md`, 사용자
   `~/.codex/skills/<name>/SKILL.md`입니다. 자세한 내용은
   [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills)을
   참고하십시오. 파일 검증은 실제 Codex Desktop/VS Code 호스트의 자동 인식을 증명하지
   않으므로, 앱을 다시 열고 `/skills` 또는 `$gameassetai-workspace`로 별도 확인합니다.

3. 설치 뒤 게임 Profile을 생성하고 선택합니다.

   ```powershell
   python -B scripts/gameassetai.py profile create <workspace> my-game `
     --name "My Game" --description "Persistent game art profile" `
     --three-d-style stylized-chibi-low-poly
   python -B scripts/gameassetai.py profile select <workspace> my-game
   python -B scripts/gameassetai.py workspace validate <workspace> --require-profile
   ```

   공식 `styles.three_d`와 `styles.two_d`에는 카탈로그의 올바른 차원 ID만 저장됩니다.
   사용자 고유의 자유로운 스타일 설명은 `art_direction` 규칙으로 관리합니다.

4. Blender와 Blender MCP 연결은 별도로 확인합니다. Skill 설치는 Blender, MCP, 외부 AI,
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

   결과는 다음 구조에 저장됩니다.

   ```text
   outputs/<active-game>/<category>/<asset-id>/<number>-<purpose>/
   ```

   카테고리는 `character`, `equipment-prop`, `environment`, `vfx-mesh` 중 하나입니다. 같은
   에셋의 수정 결과는 같은 에셋 ID에서 다음 번호를 사용합니다. 진행 중 작업을 계속하려면
   정확한 작업 경로를 `outputs continue`로 검증합니다. 날짜·UUID 이름이나 전역 카운터는
   사용하지 않습니다.

`outputs/`의 일부나 전체를 이동·삭제해도 Profile, 설치된 Skill, 카탈로그, 새 독립 작업에는
영향이 없습니다. 삭제된 특정 작업을 계속할 수는 없으며 시스템은 이를 자동 복원하지 않습니다.

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
