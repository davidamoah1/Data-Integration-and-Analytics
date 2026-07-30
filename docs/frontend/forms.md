# Forms

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Frontend Lead

---

## Purpose

Document form patterns, validation, and error handling.

## Scope

All form implementations across the frontend.

## Audience

Frontend developers.

---

## 1. Form Patterns

Forms use controlled React components with manual validation:

```tsx
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [errors, setErrors] = useState<Record<string, string>>({});

const handleSubmit = async (e: FormEvent) => {
  e.preventDefault();
  // Validate
  if (!email) setErrors(prev => ({ ...prev, email: 'Email is required' }));
  // Submit
  await login(email, password);
};
```

## 2. Common Form Components

| Form | Location | Fields |
|------|----------|--------|
| Login | `app/login/page.tsx` | email, password, remember me |
| Signup | `app/signup/page.tsx` | email, password, full_name, org_name (optional) |
| Invitation Accept | `app/invite/page.tsx` | token, email, name, password |
| Onboarding | `app/onboarding/page.tsx` | industry, org_type, primary_goal |
| Settings | `app/(app)/settings/page.tsx` | profile, appearance, security |

## 3. Validation

- **Client-side**: Manual validation in form handlers
- **Server-side**: Pydantic schemas return 422 with field-level errors
- **Display**: Inline error messages below form fields

## 4. Password Visibility Toggle

All password fields include a show/hide toggle:

```tsx
const [showPassword, setShowPassword] = useState(false);
<Input type={showPassword ? 'text' : 'password'} />
<button onClick={() => setShowPassword(!showPassword)}>
  {showPassword ? <EyeOff /> : <Eye />}
</button>
```

## 5. Error Display

- Form-level errors displayed in alert boxes
- Field-level errors displayed inline
- API errors displayed in toast notifications (Sonner)

## Related Documents

- [component-library.md](component-library.md) — Components
- [routing.md](routing.md) — Routing
- [../backend/error-handling.md](../backend/error-handling.md) — Backend error handling
