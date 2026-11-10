# GameAssetAI

GameAssetAI는 Codex Desktop 또는 VS Code + Codex에서 사용하는 스타일 기반 게임 에셋 제작
Skill 시스템입니다. Blender를 중심으로 신규 3D 에셋 제작, 기존 에셋 수정, 제한된
Rig/Animation 작업, 3D/2D 출력을 연결합니다.

현재 Repository는 제품 기반 단계입니다. 카탈로그, Asset Specification, Workspace/Profile,
안전한 결과물 run, 네 개의 독립 설치형 Skill 패키징은 동작합니다. 범용 prompt-to-3D,
모든 생물 생성, 자유형 의미 수정, 네 3D 스타일의 자동 생성, 완전한 8방향 제작은 아직
지원 완료가 아닙니다. 정확한 경계는 [Capabilities](docs/capabilities.md)를 따릅니다.

## 제품 구조

```text
catalog/                 에셋·스타일·생성 Provider 데이터
src/gameassetai/         공통 Runtime과 유지한 Blender helper
skills/                  작업 중심 제품 Skill 4개
packaging/               독립 bundle entrypoint
workspace-template/      사용자 Workspace 템플릿
blender_addon/           선택적인 Blender UI/실행 계층
scripts/                 개발 checkout 명령
tests/                   독립 offline 검증
docs/                    현재 제품·기술 기준
```

Repository는 개발·배포 원본, 설치된 Skill은 독립 실행 사본, Workspace는 게임별 설정과 사용자
결과물을 보존하는 작업 공간입니다. 기존 Blender·Unity 프로젝트와 원본/참고 파일을 Workspace
안으로 옮길 필요가 없습니다.

## 최초 설치 흐름

1. Repository checkout에서 bundle을 만들고 검증합니다.

   ```powershell
   python -B scripts/gameassetai.py package build . <bundle>
   python -B scripts/gameassetai.py package validate <bundle>
   ```

2. 네 Skill을 한 범위에 설치합니다.

   ```powershell
   # Workspace를 Codex 프로젝트로 열 때 사용하는 project scope
   python -B scripts/gameassetai.py package install <bundle> <workspace>\.codex\skills

   # 또는 모든 프로젝트에서 사용하는 user scope
   python -B scripts/gameassetai.py package install <bundle> $env:USERPROFILE\.codex\skills
   ```

   Codex 공식 경로는 project scope의 `.codex/skills/<name>/SKILL.md`와 user scope의
   `~/.codex/skills/<name>/SKILL.md`입니다. 호스트를 다시 열고 `/skills`가 제공되면 목록을
   확인하거나 새 대화에서 `$gameassetai-workspace`를 명시적으로 호출합니다. 파일 설치 성공과
   Codex Desktop/VS Code의 실제 자동 탐색은 별도 검증 단계입니다.

3. 설치된 `gameassetai-workspace` Skill로 사용자 지정 Workspace를 생성하거나 기존 Workspace를
   안전하게 연결합니다. 개발 checkout에서 직접 확인할 때는 다음 명령을 사용할 수 있습니다.

   ```powershell
   python -B scripts/gameassetai.py workspace create <workspace> --template workspace-template
   python -B scripts/gameassetai.py profile create <workspace> my-game `
     --name "My Game" --description "Persistent game art profile"
   python -B scripts/gameassetai.py profile select <workspace> my-game
   ```

4. Blender와 Blender MCP 연결을 별도로 확인합니다. Skill 설치는 Blender, MCP, 외부 AI,
   UnityWorkbench를 자동 설치하거나 설정하지 않습니다.

## 일상 사용

1. Codex Desktop 또는 VS Code + Codex에서 GameAssetAI-Workspace를 엽니다.
2. 활성 게임 Profile과 지속적인 스타일 규칙을 확인합니다.
3. 기본적으로 텍스트 설명, 스타일 프리셋, 사용자가 AI 등으로 만든 참고 이미지를 제공합니다.
   정면·측면·후면·3/4·콘셉트 등 이미지 역할을 구분합니다. 이미지가 없어도 Profile과 요청으로
   충분한지 판단하며, 필요하면 어떤 참고 자료가 필요한지 먼저 설명합니다.
4. 생성 또는 수정 요청을 하고 Blender에서 시각적 결과를 검토합니다.
5. 승인된 소스에 대해서만 출력 형식을 선택합니다.
6. 결과는 `outputs/<game>/<asset-category>/<run-id>/`에서 확인합니다.

AI 콘셉트/참고 이미지, Blender의 3D 리뷰용 프리뷰, 최종 게임 PNG·Pixel Sprite·Sprite Sheet는
서로 다른 단계입니다. `outputs/`는 사용자가 삭제할 수 있지만, 그 안의 완성 에셋 사본도 함께
삭제된다는 점과 GameAssetAI 설정·Profile·신규 작업 능력은 손상되지 않는다는 점을 구분합니다.

## Profile 갱신

일회성 요청을 게임 전체 규칙으로 저장하지 않습니다. 사용자가 지속성을 요청하거나 승인한 경우에만
특정 설정을 조회하고 갱신합니다.

```powershell
python -B scripts/gameassetai.py profile get <workspace> art_direction.palette
python -B scripts/gameassetai.py profile set <workspace> art_direction.palette `
  --value-json '["moss", "bark"]'
```

갱신은 지정하지 않은 필드를 보존하고 전체 Profile을 검증한 뒤 원자적으로 반영합니다. 구형 Markdown
Profile은 자동 변환하지 않습니다. 자세한 운영 절차는 [Workspace guide](docs/workspace.md)를
참조하십시오.

## 개발 검증

```powershell
python -B scripts/validate_repo.py
python -B -m unittest discover -s tests -p "test_*.py" -v
```

GitHub Actions는 Linux와 Windows에서 같은 offline 기반 검증을 실행합니다. 이 검증은 실제 Blender
시각 품질, MCP 실행, Codex 호스트 탐색, Unity round trip을 증명하지 않습니다.

## 문서

- [Product definition](docs/product-definition.md)
- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Capabilities](docs/capabilities.md)
- [Workspace](docs/workspace.md)
- [Distribution](docs/distribution.md)
- [Quality and testing](docs/quality.md)
- [Roadmap](docs/roadmap.md)
