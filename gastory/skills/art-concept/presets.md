# Art Concept Presets

Each preset defines defaults for a project's visual style. When the user picks a preset, copy these fields into `art-concept.json`.

---

## 2d-anime

- **render_style**: `2D digital illustration, anime style, clean lineart`
- **background_default**: `plain white background`
- **framing_default**: `full body shot`
- **quality_keywords**: `high quality, detailed lineart, vibrant colors`
- **recommended_use**: 캐릭터 스프라이트, RPG 캐릭터 카드, 게임 아이콘

---

## 2d-pixel

- **render_style**: `pixel art, 16-bit retro game style, limited color palette`
- **background_default**: `transparent background`
- **framing_default**: `side view, full body`
- **quality_keywords**: `crisp pixels, no anti-aliasing, sharp edges`
- **recommended_use**: 레트로 게임 캐릭터/타일/아이템

---

## 2d-painterly

- **render_style**: `2D painterly illustration, soft brushwork, expressive`
- **background_default**: `atmospheric soft gradient background`
- **framing_default**: `full body, three-quarter view`
- **quality_keywords**: `rich textures, painterly detail, depth of field`
- **recommended_use**: 스토리북 스타일 게임, 어드벤처 게임, 핸드 페인티드 RPG

---

## 3d-render

- **render_style**: `3D rendered, modern game asset, PBR materials`
- **background_default**: `plain neutral gray background`
- **framing_default**: `full body, slight three-quarter angle`
- **quality_keywords**: `high detail, soft studio lighting, sharp focus`
- **recommended_use**: AAA 스타일 캐릭터, 모던 3D 게임

---

## cartoon

- **render_style**: `2D cartoon illustration, bold outlines, simple flat shading`
- **background_default**: `plain white background`
- **framing_default**: `full body shot`
- **quality_keywords**: `vibrant flat colors, expressive features, clean shapes`
- **recommended_use**: 캐주얼 게임, 모바일 게임, 어린이용 게임

---

## custom

User-provided free-form style description. There are no fixed fields; instead:

- **render_style**: 사용자가 직접 묘사한 텍스트 그대로
- **background_default**: 사용자에게 물어봄 (없으면 `plain white background` 추천)
- **framing_default**: 사용자에게 물어봄 (없으면 `full body shot` 추천)
- **quality_keywords**: 사용자에게 추가하고 싶은 품질 관련 표현이 있는지 물음
- **additional_notes**: 그 외 적용하고 싶은 모든 것 (테마, 컬러 톤, 시대 배경 등)
