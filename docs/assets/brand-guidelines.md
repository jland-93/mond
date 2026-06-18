# 🌙 Mond Brand Guidelines

## 🎨 Brand Identity

Mond represents the gentle guidance of moonlight in the darkness of complex security landscapes. Our brand embodies trust, intelligence, and approachability.

### Brand Personality
- **Gentle**: Non-intrusive and developer-friendly
- **Intelligent**: AI-powered and data-driven
- **Reliable**: Always there when needed
- **Illuminating**: Provides clarity in complexity

## 🎨 Visual Identity

### Logo Usage
The Mond logo (`docs/assets/images/mond-logo.png`) is shipped in a single PNG. App icons are derived from it and live under `frontend/public/`:
- `logo.png` — 192×192 inline logo (sidebar, login card)
- `logo-{32,64,96,180,192,512}.png` — favicon / Apple touch / PWA icons
- `og-image.png` — 512×512 Open Graph card
- `favicon.png` — alias for `logo-64.png`
- `apple-touch-icon.png` — alias for `logo-180.png`

### Logo Guidelines
- **Minimum Size**: 120px width for digital, 1 inch for print
- **Clear Space**: Maintain clear space equal to the height of the moon symbol
- **Don't**: Stretch, rotate, or modify colors without approval

## 🌈 Color Palette

### Primary Colors
```css
/* Deep Night Blue - Primary brand color */
--mond-primary: #1a237e;
--mond-primary-rgb: 26, 35, 126;

/* Moonlight Blue - Secondary accent */
--mond-secondary: #3f51b5;
--mond-secondary-rgb: 63, 81, 181;

/* Silver Glow - Highlight color */
--mond-accent: #e8eaf6;
--mond-accent-rgb: 232, 234, 246;
```

### Supporting Colors
```css
/* Dark Navy - Background */
--mond-dark: #0d1421;
--mond-dark-rgb: 13, 20, 33;

/* Soft Gray - Text secondary */
--mond-gray: #64748b;
--mond-gray-rgb: 100, 116, 139;

/* Pure White - Text primary */
--mond-white: #ffffff;
--mond-white-rgb: 255, 255, 255;
```

### Status Colors
```css
/* Success - Gentle Green */
--mond-success: #10b981;
--mond-success-rgb: 16, 185, 129;

/* Warning - Warm Amber */
--mond-warning: #f59e0b;
--mond-warning-rgb: 245, 158, 11;

/* Error - Soft Red */
--mond-error: #ef4444;
--mond-error-rgb: 239, 68, 68;

/* Info - Cool Blue */
--mond-info: #3b82f6;
--mond-info-rgb: 59, 130, 246;
```

## 🔤 Typography

### Primary Font Stack
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
```

### Font Weights
- **Light (300)**: Large headings, elegant displays
- **Regular (400)**: Body text, descriptions
- **Medium (500)**: Subheadings, emphasis
- **Semibold (600)**: Section headers, navigation
- **Bold (700)**: Main headings, CTAs

### Code Font
```css
font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', 'Consolas', monospace;
```

## 🎭 Iconography

### Icon Style
- **Style**: Outline icons with 2px stroke width
- **Corner Radius**: 2px for consistency
- **Size**: 16px, 20px, 24px, 32px standard sizes
- **Color**: Use brand colors or neutral grays

### Moon Phase Icons
Special moon phase icons represent different states:
- 🌑 **New Moon**: Starting/initializing
- 🌒 **Waxing Crescent**: In progress (0-25%)
- 🌓 **First Quarter**: In progress (25-50%)
- 🌔 **Waxing Gibbous**: In progress (50-75%)
- 🌕 **Full Moon**: Complete/optimal
- 🌖 **Waning Gibbous**: Declining/warning
- 🌗 **Last Quarter**: Critical/attention needed
- 🌘 **Waning Crescent**: Minimal/ending

## 📱 UI Components

### Buttons
```css
/* Primary Button */
.btn-primary {
  background: var(--mond-primary);
  color: var(--mond-white);
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 500;
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: var(--mond-primary);
  border: 2px solid var(--mond-primary);
  border-radius: 8px;
  padding: 10px 22px;
  font-weight: 500;
}
```

### Cards
```css
.card {
  background: var(--mond-white);
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--mond-accent);
}
```

### Dark Theme
```css
.dark-theme {
  --background: var(--mond-dark);
  --surface: #1e293b;
  --text-primary: var(--mond-white);
  --text-secondary: var(--mond-gray);
}
```

## 📐 Layout & Spacing

### Grid System
- **Container Max Width**: 1200px
- **Breakpoints**: 
  - Mobile: 320px - 768px
  - Tablet: 768px - 1024px
  - Desktop: 1024px+

### Spacing Scale
```css
--space-1: 4px;   /* 0.25rem */
--space-2: 8px;   /* 0.5rem */
--space-3: 12px;  /* 0.75rem */
--space-4: 16px;  /* 1rem */
--space-6: 24px;  /* 1.5rem */
--space-8: 32px;  /* 2rem */
--space-12: 48px; /* 3rem */
--space-16: 64px; /* 4rem */
```

## 🖼️ Photography & Imagery

### Style Guidelines
- **Mood**: Calm, professional, trustworthy
- **Color Treatment**: Cool tones, blue/purple palette
- **Composition**: Clean, minimal, focused
- **Lighting**: Soft, even lighting (like moonlight)

### Image Types
- **Hero Images**: Abstract tech patterns with blue gradients
- **Feature Images**: Clean UI screenshots with subtle shadows
- **Team Photos**: Professional but approachable
- **Illustrations**: Minimal line art with brand colors

## 📝 Voice & Tone

### Brand Voice
- **Knowledgeable**: Expert but not condescending
- **Helpful**: Solution-oriented and supportive
- **Calm**: Reassuring in stressful situations
- **Clear**: Simple, jargon-free communication

### Tone Variations
- **Documentation**: Clear, instructional, comprehensive
- **Marketing**: Inspiring, benefit-focused, confident
- **Support**: Patient, empathetic, solution-focused
- **Social**: Friendly, engaging, community-minded

### Writing Guidelines
- Use active voice when possible
- Keep sentences concise and clear
- Avoid technical jargon unless necessary
- Include examples and practical applications
- End with actionable next steps

## 🚫 Brand Don'ts

### Visual Don'ts
- Don't use harsh, bright colors
- Don't use aggressive or intimidating imagery
- Don't overcomplicate layouts
- Don't use more than 3 colors in one design

### Voice Don'ts
- Don't be condescending or overly technical
- Don't create fear or anxiety about security
- Don't make promises you can't keep
- Don't ignore user feedback or concerns

## 📊 Brand Applications

### Digital Applications
- Website and web applications
- Mobile applications
- Social media profiles and posts
- Email templates and signatures
- Digital presentations

### Print Applications
- Business cards and stationery
- Conference materials and swag
- Technical documentation
- Marketing collateral

---

**Remember: Mond illuminates the path to secure DevOps with gentle, intelligent guidance. Every brand touchpoint should reflect this core promise.** 🌙✨

---

## 🧭 문서 한눈에 · Doc Map

| 문서 | 무엇 |
|---|---|
| 🏠 [`/README.md`](../../README.md) | 프로젝트 소개 · 스크린샷 |
| 🌙 [`ABOUT.md`](../ABOUT.md) | 왜 만들었나 · 무엇을 푸는가 · 로드맵 |
| 🛠️ [`SETUP.md`](../SETUP.md) | 설치 · 운영 · 시나리오 가이드 |
| 🏗️ [`development/architecture.md`](../development/architecture.md) | 시스템 구조 |
| 🎨 [`assets/brand-guidelines.md`](brand-guidelines.md) (이 문서) | 로고 · 컬러 · 타이포 |
| 🤝 [`/CONTRIBUTING.md`](../../CONTRIBUTING.md) | 기여 가이드 |
| 📋 [`/CHANGELOG.md`](../../CHANGELOG.md) | 변경 내역 |
