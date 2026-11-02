# GameAssetAI repository review — 2026-11-02

## 1. 결론

GameAssetAI의 본래 목적은 Codex 같은 AI 에이전트가 재사용 가능한 Skill과 Blender를
이용해 **서로 다른 게임의 3D 에셋을 생성·수정·리깅·애니메이션 처리하고, 필요하면
2D와 Unity 출력까지 연결하는 제작 시스템**을 제공하는 것이다. 현재 Repository는
이 목적의 기술 기반 일부를 잘 구현했지만, 제품의 중심인 범용 제작 능력은 충분히
구현하지 못했다.

현재 강점은 다음과 같다.

- 명시적 요청 계약, 입력 해시, 원본 보존, 작업 사본, rollback, no-overwrite publication
- Blender Background/Python 실행과 로컬 Skill 설치·갱신 체계
- 제한된 인간형 리깅, 실제 Mixamo Action import/retarget, Action clip preparation
- Generic animated FBX의 Blender round-trip 및 실제 Unity 검증
- 결정론적인 2D render/pass/sequence/sprite-sheet 파이프라인

현재 핵심 결손은 다음과 같다.

- 자연어 형상 설명을 다양한 실루엣·부품·표면으로 변환하는 일반 정적 모델 제작
- 머리카락·의상·장비·크리처를 포함하는 캐릭터 제작 및 기존 모델의 의미 기반 편집
- 게임별 art direction을 geometry, topology, material, texture에 실제로 반영하는 계층
- texture/UV authoring과 Hand-painted, Anime, Chibi, PS1, realistic/PBR 제작 능력
- 생성부터 검토·수정·출력까지 연결하는 작은 사용자용 제품 표면

따라서 권장안은 **B: Repository와 검증된 기반은 유지하되 핵심 제작 계층을
재설계**하는 것이다. 전체 재출발은 검증된 안전·설치·애니메이션·출력 코드를
불필요하게 버린다. 반대로 현 구조를 그대로 확장하면 narrow validator와 변환 Skill의
수가 다시 늘고, 실제 제작 결손은 남는다.

이 감사는 기존 완료 보고를 그대로 인정하지 않았다. 기준선 HEAD의 추적 파일 618개를
열거하고 SHA-256으로 고정했으며, 모든 46개 `SKILL.md`, 실행 계약, Python 정적 구조,
핵심 구현, Add-on, 주요 테스트와 문서의 실제 내용을 검토했다. 파일별 검토 수준은
`2026-11-02-file-review.tsv`에 공개한다. 모든 파일을 동일한 깊이로 line-by-line
검토했다고 주장하지 않는다. 동일 해시/정규화 동일 사본은 대표 내용을 검토하고 각
경로의 배포 맥락을 별도로 판정했으며, 단순 fixture와 생성 자료는 인덱스·정적 의미
검토로 표시했다.

## 2. 감사 기준선과 방법

| 항목 | 값 |
|---|---|
| Branch | `master` |
| HEAD | `332bd05b523c5cc8365af78b3543fb6ca70ca401` |
| Remote | `https://github.com/jiwoo7158/GameAssetAI.git` |
| 시작 상태 | clean |
| 추적 파일 | 618 |
| 추적 용량 | 4,542,017 bytes |
| Skill 폴더 | 46 |
| Python / Markdown | 468 / 140 |
| tests / scripts / Add-on / docs 파일 | 127 / 121 / 14 / 77 |
| 정확히 동일한 hash 그룹 | 94 groups, 229 paths |
| newline/BOM 정규화 후 동일 그룹 | 103 groups, 305 paths |

검토 절차:

1. `git ls-files` 기준으로 전체 목록·크기·SHA-256을 생성했다.
2. Markdown 계약과 문서, Python AST/import/function/class, JSON/YAML/C# 설정을 모두
   인덱싱했다.
3. 모든 Skill 계약은 개별적으로 읽고 책임·실행 파일·관계·증거·한계를 판정했다.
4. 같은 이름의 root/Skill Python은 정규화 후 실제 내용이 같은지 비교했다.
5. 핵심 creation/rig/animation/export 구현과 대표 Blender/Unity 테스트는 직접
   내용 검토했다.
6. 문서의 완료 주장을 코드와 테스트가 실제로 확인하는 범위에 맞춰 재판정했다.

상세 파일 기록은 [file review](2026-11-02-file-review.tsv), Skill 판정은
[skill assessment](2026-11-02-skill-assessment.tsv)에 있다. 두 표는 감사 시작 시점의
HEAD를 기준으로 하므로 이번 감사에서 새로 생성한 세 파일 자체는 기준선 목록에
포함하지 않는다.

## 3. 원래 목표와 현재 달성도

### 3.1 목표 재구성

`AGENTS.md`, `docs/requirements.md`, `docs/architecture.md`, Workspace 계약과 실제 코드가
공통으로 가리키는 제품은 다음 흐름이다.

```text
자연어 제작/수정 요청
  -> 작은 사용자용 workflow surface
  -> Blender에서 모델·재질·rig·animation 생성 또는 기존 자료 수정
  -> 실제 Scene에서 semantic/visual review와 reversible revision
  -> 선택적 2D 변환
  -> Unity 중심 export/import
```

Repository는 “게임 에셋 모음”이 아니라 이 작업을 재사용 가능하게 만드는 Skill
프로젝트다. 기존 에셋은 일급 입력이며, 모든 것을 처음부터 생성할 필요는 없다.

### 3.2 달성도 판정

| 제품 계층 | 판정 | 실제 근거 |
|---|---|---|
| 설치·패키징·Workspace | 강함 | `scripts/deploy_skill.py`, `update_skill.py`, 배포 검증 테스트 |
| 안전한 Blender 변경 | 강함 | ownership, copy, rollback, no-overwrite 계약이 다수 Skill에 반복 적용 |
| 정적 모델 생성 | 제한적 | 4 primitive의 명시적 assembly와 소유 object 비율 revision |
| 캐릭터 생성 | 실험적/제한적 | blockout과 hash-pinned CC0 human template proportion warp |
| 기존 임의 에셋 수정 | 약함 | 범용 mesh/material/UV semantic editor 없음 |
| Rig/weight | 제한된 대표 범위 | 명시적 22 landmark A-pose, 18-bone, envelope 기반 |
| Animation import/edit | 중간 이상 | 실제 Mixamo Walking, 독립 Action, clip sampling/cleanup |
| 2D 변환 | 기술적으로 강함 | deterministic render/pass/sequence/sheet, 다만 미술 품질 증거 부족 |
| Unity output | 제한적으로 강함 | static 및 Generic animated FBX; Humanoid Avatar 미승인 |
| 아트 스타일 | 매우 약함 | profile/필드는 있으나 geometry/texture 생성과 연결되지 않음 |
| Add-on 제품 UI | 부분적 | 2D preview/setup/export 중심; creation/rig/M3/M4 UI는 없음 |
| 자연어 orchestration | 약함 | router는 실행 코드가 없는 instruction-only Skill |

즉, “에셋을 안전하게 처리하고 전달하는 능력”은 상당하지만 “요청한 에셋을 실제로
만드는 능력”은 좁다. 현재 상태를 범용 게임 에셋 제작 시스템이라고 부르기에는
제작 종류와 스타일 증거가 부족하다.

## 4. 실제 게임 에셋 제작 능력

| 유형 | 신규 생성 | 기존 수정 | 실제 방식과 한계 | 증거 수준 |
|---|---|---|---|---|
| 검·도끼·창 등 무기 | 제한적 | 소유 assembly의 부품 transform만 | BOX/CYLINDER/ICOSPHERE/WEDGE 조합. 날 profile, 곡면 장식, 세부 topology를 자연어로 생성하지 못함 | 검/야전포 계열 대표 실험, 범용성 미승인 |
| 방패·헬멧·갑옷 | 매우 제한적 | 범용 수정 없음 | primitive로 단순 방패는 표현 가능하나 착용·곡면·fit 계약 없음 | 미검증 |
| 상자·통·랜턴·도구 | 제한적 | v2.1 semantic role의 치수·위치·회전 | 명시적 다부품 low-poly prop은 가능. arbitrary shape/UV/texture 없음 | 랜턴 및 구조가 다른 prop 집중 증거 |
| 의자·책상·캐비닛 | 제한적 | 조립품 범위만 | 직선형 primitive 가구는 요청을 수동 part spec으로 번역해야 함 | 대표 증거 없음 |
| 기계·차량 부품·장치 | 제한적 | 조립품 범위만 | 단순 hard-surface blockout 가능, mechanical detail/boolean workflow 없음 | Kiln GLB adapter는 생성기가 아님 |
| 벽·울타리·문·건물 | 제한적 | 범용 수정 없음 | 단순 모듈 형상 가능, architectural system 없음 | 미검증 |
| 바위·나무·식생·지형 | 사실상 불가 | 범용 수정 없음 | organic/procedural environment generator 없음 | 미검증 |
| 인간형 캐릭터 | 제한적 | 비율 warp만 | v1/v3 blockout, v4 CC0 human template의 region scaling. 얼굴·손·헤어·의상·style authoring 없음 | Compact/Lanky 기술 검증; 제품 품질 범위 제한 |
| 동물·몬스터·비인간형 | 불가 | 없음 | humanoid template/rig 계약에 종속 | 증거 없음 |
| 헤어·의상·장비 | 불가 | 없음 | 생성·fit·skin/cloth 계약 없음 | 증거 없음 |
| 자체 애니메이션 | 매우 제한적 | 명시 pose/action 작업 | explicit pose keys는 가능, motion synthesis/IK authoring 없음 | 일부 대표 action |
| 기존 Action 편집 | 지원 | 비파괴 clip 생성 | range sampling, rebase, quaternion continuity, bounded cleanup | 실제 M3.3 Walking과 합성 action |
| Retarget | 제한 지원 | 지원 | 명시 17-role Mixamo, M2 target, single Action, IN_PLACE | 실제 Adobe Walking accepted 범위 |
| Pixel/Cel 2D | 변환 지원 | 설정 변경 지원 | 3D source render, palette/value/outline/pass/sheet. 2D 도안 생성기는 아님 | host/synthetic 중심 |
| FBX/Rig/Animation | 지원 | 해당 없음 | static FBX와 bounded Generic animated FBX | Blender round-trip, 실제 Unity Generic |

`scripts/validate_static_asset_assembly_request.py`의 primitive 허용 집합과
`scripts/create_static_asset_assembly.py`의 `create_asset`, `revise_asset_copy`, GLB import
경로가 정적 제작의 실제 상한을 보여준다. Kiln adapter는 검증된 외부 GLB를 안전하게
가져오는 경계이며 Kiln을 실행하거나 자연어 모델을 생성하지 않는다.

## 5. 아트 스타일 지원 평가

스타일 이름·profile field·render preset의 존재와 실제 art direction 제작 능력을
구분해야 한다.

| 스타일 | 현재 지원 | 이유 |
|---|---|---|
| 단순 Low-Poly | 제한 지원 | primitive assembly, flat/basic material, poly가 낮은 blockout |
| Stylized Low-Poly | 약함 | 실루엣/비율을 명시 수치로 일부 조절할 수 있으나 style grammar가 없음 |
| Cartoon | 출력 셰이딩만 일부 | Add-on CEL_BANDED/flat preview는 가능하나 cartoon geometry/texture 생성 없음 |
| Anime / Toon | 출력 셰이딩만 일부 | toon render와 anime character mesh/face/hair 제작은 별개이며 후자는 없음 |
| SD / Chibi | 미지원 | 체형 profile이 chibi topology, head/face, hand/foot design으로 연결되지 않음 |
| Hand-painted | 미지원 | texture 생성·painting·UV authoring pipeline 없음 |
| PS1 / Retro 3D | 미지원에 가까움 | poly/texture resolution/vertex jitter/affine look를 통합하는 제작 계약 없음 |
| Realistic / PBR | 미지원 | 기본 Principled 값 외에 texture set, material scan/detail 제작 없음 |
| Pixel/Cel 2D 출력 | 제한 지원 | accepted 3D source를 deterministic하게 변환; pixel art 자체의 설계는 아님 |

Workspace profile은 project-specific 설정의 올바른 저장 위치지만, 일반 생성 코드가
profile의 art direction, polygon budget, texture policy를 소비하지 않는다. 구체적 resolver가
검증된 영역은 주로 2D preset이다. Blender Studio Human Base Meshes를 사용한 M1~M4
캐릭터는 topology/rig/animation/export 검증용 source일 뿐 GameAssetAI의 기본 미술
스타일로 승인된 것이 아니다.

## 6. Skill 포트폴리오 평가

46개 폴더는 46개 제품 기능이 아니다. 다수는 안전하게 한 단계를 수행하는 내부
helper이고, 사용자가 자연어 요청마다 직접 조합해야 할 대상이 아니다.

| 권장 상태 | 수 | 의미 |
|---|---:|---|
| `KEEP_CORE` | 7 | 현재 사용자 workflow에서 직접 가치가 있는 기능 |
| `KEEP_INTERNAL` | 15 | 핵심 workflow가 호출할 inspection/copy/bake helper |
| `CONSOLIDATE` | 8 | 구현은 보존하되 사용자 표면에서는 상위 workflow로 감출 대상 |
| `FREEZE` | 10 | 유효하지만 core creation보다 추가 개발 우선순위가 낮음 |
| `REWORK` | 5 | 제품 목표에 맞게 책임·입력·실제 제작 능력을 크게 보강할 대상 |
| `DEPRECATE` | 1 | 현재 기본 경로에서 제외할 근거가 있는 과거 실험 기능 |
| `REMOVE_CANDIDATE` | 0 | 이번 감사만으로 즉시 삭제할 정도의 근거는 없음 |

세부 판정과 각 Skill의 요구사항, entrypoint, relation, test/evidence, limitation, 근거
경로는 `2026-11-02-skill-assessment.tsv`가 단일 기준이다.

핵심 판정:

- `blender-create-game-asset`: 제품 진입점으로 필요하지만 실행 orchestration이 없는
  instruction-only router이므로 `REWORK`.
- `blender-create-static-asset`, `blender-create-character-base`,
  `blender-rig-character-base`: 제작 spine이지만 일반성·style·existing asset 범위가
  좁아 `REWORK`.
- `blender-import-humanoid-animation`, `blender-prepare-game-action`,
  `blender-export-animated-fbx`: 실제 대표 경로가 있어 `KEEP_CORE`.
- 좁은 animation inspect/copy/bake/compose Skill: 코드 책임은 유효하나 제품 UI에서는
  `KEEP_INTERNAL` 또는 `CONSOLIDATE`.
- object/material mask, normal/depth/object-id, impostor, collider/LOD diagnostics:
  기술적으로 유효하지만 creation 결손보다 우선하지 않도록 `FREEZE`.
- `blender-adjust-character-joint-weights-copy`: rejected source에서 얻은 과거 실험이며
  M2 weighting과 역할이 겹치므로 `DEPRECATE`.

즉시 삭제를 권하지 않는 이유는 독립 패키징·rollback 경계와 이미 재사용되는 helper가
있기 때문이다. 다음 단계에서 router surface와 호출 graph를 먼저 정리한 뒤 physical
통합·삭제를 별도 승인해야 한다.

## 7. 코드 구조와 중복

### 7.1 중복의 성격

root `scripts/`와 Skill 내부 Python 사본은 BOM/newline을 제외하면 같은 내용이었다.
`tests/scripts/test_development_tools.py`도 여러 root/packaged 쌍의 정규화 동등성을
명시적으로 검사한다. 따라서 현재 중복은 대부분 독립 Skill ZIP을 위한 배포 사본이지,
서로 다른 알고리즘이 우연히 중복된 것은 아니다.

문제는 source authority와 update 경로가 구조적으로 명확하지 않다는 점이다. 동일 내용을
여러 위치에서 직접 편집할 수 있고, equality test가 누락된 신규 사본은 drift할 수 있다.
장기적으로는 canonical source에서 package를 생성하는 방식이 적절하지만, 이번 감사에서
대규모 packaging 변경은 하지 않는다.

### 7.2 아키텍처 판정

유지할 가치가 높은 부분:

- Skill별 bounded contract와 명시적 failure policy
- Blender native API 우선, background 실행
- ownership/preservation/rollback/no-overwrite publication
- Workspace와 Repository 분리
- external input hash/provenance
- focused Blender/Unity round-trip tests
- artifact lifecycle

재설계가 필요한 부분:

- instruction-only router를 실제 작은 workflow surface로 만드는 orchestration
- static/character/existing-asset revision의 표현력
- style profile에서 geometry/material/texture 제작까지 이어지는 연결
- Add-on을 2D panel에서 creation/revision/review 실행 계층으로 확장하는 계획
- internal helper와 user-facing Skill의 명시적 구분
- canonical source와 packaged copy의 생성 관계

Validator가 복잡한 이유 중 상당 부분은 원본 보호와 외부 publication에는 정당하다.
그러나 검사·패스·export의 계약 정밀도가 생성 계약보다 훨씬 앞서 있고, cube/synthetic
fixture가 semantic capability처럼 읽힌 과거 보고 방식은 제품 우선순위를 왜곡했다.

## 8. 검증 증거의 신뢰성

| 영역 | 코드/단위 | Blender 실물 | 시각 승인 | Engine | 이번 판정 |
|---|---|---|---|---|---|
| Static assembly/revision | 있음 | 대표 prop 있음 | 제한적 | static FBX 별도 | primitive assembly 범위만 대표 |
| Character v3/v4 | 있음 | Compact/Lanky | 제한·일부 rejected history | M4 source | 범용 character quality 아님 |
| M2 rig fitting | 있음 | 두 비율 template | bounded pose review | 간접 | 명시 22-landmark A-pose만 accepted |
| M3.3 Mixamo | 있음 | 실제 Adobe Walking | 명시 이미지 review | 아님 | 17-role M2/IN_PLACE/single Action 범위 |
| M3.4 Action prep | 있음 | 실제 Walking clip | pose preservation 측정 | 아님 | representative |
| M4 animated FBX | 있음 | Blender reimport | sampled deformation | 실제 Unity Generic | Generic engine-proven; Humanoid 아님 |
| Add-on | source/test 있음 | persistence install 기록 | UI 품질 제한 | 해당 없음 | 설치 가능, 제품 범위는 2D 중심 |
| 2D pipeline | 강한 테스트 | host/cube 다수 | 미술 품질 승인 부족 | Unity slicing 아님 | plumbing/encoding 대표, art quality 미증명 |

구조 검사, vertex displacement, file creation은 자연스러운 움직임이나 좋은 모델을
증명하지 않는다. 반대로 실제 Adobe FBX와 Unity validator를 사용한 M3/M4의 bounded
증거는 합성 fixture보다 강하다. `engine-proven`은 Generic import/playback 범위에만
유효하며 Humanoid Avatar, seamless loop, broad rig support로 확대하면 안 된다.

`scripts/validate_repo.py`는 필수 파일·구문·contract structure를 검사한다. 미술 품질이나
semantic capability validator가 아니므로 repository validation 통과를 제품 완료로
해석하지 않는다.

## 9. Blender Add-on과 자연어 사용성

Add-on 0.1.5는 source와 persistence 설치 증거가 있다. 그러나 실제 panel/operator는
Pixel Scene Setup, compositor, material preview, Action preview, PNG/sequence/sprite sheet
bridge가 중심이다. static creation, character creation, rig fitting, retarget, Action cleanup,
animated export를 반복 실행하는 일반 제작 UI는 아직 아니다.

또한 `blender-create-game-asset`은 자연어 의도 분류 지침을 제공하지만 실행 가능한
workflow coordinator는 아니다. 46개 중 `agents/openai.yaml`이 있는 Skill도 극소수다.
Codex의 자연어 discovery는 가능하지만 일관된 end-to-end 호출을 보장하는 제품 계층은
부족하다. 사용자가 narrow helper를 직접 알아야 하는 구조는 내부 모듈성과 별개로
제품 사용성 문제다.

## 10. 문서 감사

### 현재 필수 문서

- `AGENTS.md`
- `docs/requirements.md`
- `docs/architecture.md`
- `docs/skill-design.md`
- `docs/IMPLEMENTATION_MEMORY.md`
- `docs/roadmap.md`
- 짧은 `docs/SESSION_STATE.md`
- 이번 감사 보고서와 두 TSV

### 기술 참고/증거

- 각 validation/round-trip 문서
- open-source evaluation 기록
- `docs/session-history/`

### 역사적 문서로 내려야 하는 것

- `docs/PROJECT_AUDIT.md`: 2026-10-25 recovery 판단. 당시에는 유효했지만 현재 Skill 수,
  M1~M4 상태와 다름.
- `docs/SKILL_REUSE_AUDIT.md`: 43 Skill 시점의 포트폴리오 판단.
- 이전 session log와 rejected experiment 문서.

### 확인된 혼란

- README의 Add-on “persistent install 미증명” 경고는 이후 0.1.5 증거와 충돌했다.
- recovery audit가 자신을 “corrective source of truth”라고 선언해 최신 코드보다 오래된
  2026-10-25 판단이 우선될 수 있었다.
- `SESSION_STATE.md`가 다시 800줄 이상으로 성장해 active checkpoint와 역사가 섞였다.
- router의 pipeline reference는 v3/pre-Mixamo 상태를 기술해 M2~M4와 불일치한다.
- README와 일부 문서의 mojibake가 가독성을 해친다.

이번 감사에서는 README와 핵심 상태 문서의 권위·현재 상태만 바로잡는다. validation
history를 대량 삭제하지 않으며 Skill 계약 변경은 Workspace 설치본과의 hash alignment를
요구하므로 별도 구조 개선 작업으로 남긴다.

## 11. 구조 선택지

| 선택 | 장점 | 비용/위험 | 판정 |
|---|---|---|---|
| A. 현 Repository 그대로 점진 확장 | migration 최소, 기존 테스트 유지 | narrow Skill/validator 증가, creation/style 결손 지속 | 비권장 |
| B. Repository 유지 + 핵심 제작 계층 재설계 | 안전·설치·animation/export/2D 재사용, 목표에 직접 투자 | router/creation/style/Add-on surface 마이그레이션 필요 | **권장** |
| C. 새 구조로 재출발 | 깨끗한 API 설계 가능 | 검증된 rollback/export/installation 손실, 이중 유지·migration 위험 | 현재 근거로 비권장 |

권장 B의 경계:

1. 기존 Skill을 즉시 삭제하지 않는다.
2. user-facing surface를 static creation/revision, character creation/revision,
   existing-character rig/animation, engine export, optional 2D로 제한한다.
3. narrow inspector/bake/pass는 내부 dependency graph로 이동한다.
4. 다음 구현은 validator가 아니라 실제 제작 표현력 하나를 대표 에셋과 시각 승인까지
   완성해야 한다.
5. Add-on은 검증된 Skill의 반복 실행/review layer로 연결하되 별도 기능을 재구현하지 않는다.

## 12. 다음 개발 전에 필요한 사용자 결정

다음은 코드가 자동으로 정할 제품 선택이 아니다.

1. 첫 재설계 대상: 정적 prop/weapon 제작과 기존 mesh revision을 먼저 할지, character
   style/garment 제작을 먼저 할지.
2. 첫 대표 art direction: 모든 게임의 기본값이 아니라 capability를 입증할 하나의
   bounded target(예: stylized low-poly prop family)을 정할지.
3. 사용자용 Skill surface: 제안된 다섯 workflow를 승인할지.
4. 기존 narrow Skill의 physical consolidation/deprecation을 언제 수행할지.
5. Add-on 다음 범위: creation/revision/review 중 무엇을 먼저 UI에 노출할지.
6. Generic Unity 경로 다음에 Humanoid Avatar를 우선할지, 제작 표현력을 우선할지.

제품 목표 관점에서는 1번과 2번을 먼저 정하고 실제 생성·수정 품질을 개선하는 것이
타당하다. M4 이후 추가 export validator나 render pass를 먼저 늘리는 것은 권하지 않는다.

## 13. 이번 감사에서 변경한 것

- `docs/audits/2026-11-02-repository-review.md`: 본 감사 결론
- `docs/audits/2026-11-02-file-review.tsv`: 기준선 618개 추적 파일의 hash/역할/검토 수준
- `docs/audits/2026-11-02-skill-assessment.tsv`: 46개 Skill 개별 판정
- `README.md`: 최신 audited status와 Add-on 경고 수정
- `docs/PROJECT_AUDIT.md`, `docs/SKILL_REUSE_AUDIT.md`: 역사적 recovery 문서로 권위 조정
- `docs/IMPLEMENTATION_MEMORY.md`, `docs/roadmap.md`: B안과 다음 제품 gate 반영
- `docs/SESSION_STATE.md`: 짧은 active checkpoint로 복원하고 기존 내용을 history로 보존

Skill, 실행 코드, 테스트, Workspace 설치본은 변경하지 않았다. Skill 삭제·대규모 통합,
Workspace 제거, Git commit/push도 수행하지 않았다.

## 14. 최종 직접 답변

1. **본래 목적:** 다양한 게임에 맞는 에셋을 자연어와 Blender Skill로 제작·수정·검토하고
   엔진에 전달하는 재사용 가능한 제작 시스템이다.
2. **충족 정도:** 안전한 처리·animation·export 기반은 의미 있게 달성했지만, 범용 생성과
   style 제작이 약해 제품 전체로는 부분 달성이다.
3. **만들 수 있는 것:** 명시 primitive assembly prop, fixed-template humanoid variation,
   bounded rig/animation clip, 2D render outputs, Generic animated FBX. 일반 organic/creature/
   clothing/textured stylized asset은 만들지 못한다.
4. **현재 스타일의 원인:** character는 Blender Studio human topology와 region warp,
   prop은 primitive/material parameter에 의해 형상이 정해지기 때문이다.
5. **게임별 style:** profile 개념은 있으나 실제 geometry/texture generator 연결이 없어
   아직 실질적으로 지원하지 못한다.
6. **핵심/불필요 Skill:** 7 core, 15 internal, 8 consolidate, 10 freeze, 5 rework,
   1 deprecate. 상세는 TSV가 기준이다.
7. **미검증 Skill:** 다수 narrow Skill은 synthetic/host test뿐이며 TSV에서 evidence와
   maturity를 명시했다. 특히 broad modeling/style claims는 미검증이다.
8. **분리/중복:** 사용자 표면은 과도하게 분리됐다. 코드 복사는 주로 package 사본이지만
   canonical generation이 없어 유지보수 위험이 있다.
9. **혼란 문서:** README의 stale Add-on 경고, 2026-10-25 audit들의 현재 권위, 비대해진
   SESSION_STATE, 오래된 router pipeline이다.
10. **완료 주장 일치:** bounded M3/M4 주장은 대체로 실제 증거가 있으나 character/style/
    2D art quality로 확대된 해석은 코드·증거와 일치하지 않는다.
11. **유지 가치:** installation, contracts, rollback, ownership, animation helpers,
    M3/M3.4, Generic FBX/Unity, deterministic 2D, artifact lifecycle.
12. **재설계 대상:** creation/revision/style, router orchestration, Add-on product surface,
    package source authority. narrow helpers는 통합 노출한다.
13. **합리적 선택:** B, Repository 유지 + 핵심 제작 계층 재설계.
14. **실제 수정:** 위 13절의 감사·핵심 상태 문서만 수정했다.
15. **사용자 결정:** 첫 제작 domain과 대표 art direction, 작은 사용자용 workflow surface,
    consolidation/Add-on/Unity Humanoid 우선순위다.

