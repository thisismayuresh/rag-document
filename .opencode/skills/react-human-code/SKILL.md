---
name: react-human-code
description: Use when writing or editing any React/TypeScript code in this repo (frontend/, hooks, components, fetch layers). Encforces human-readable code style rules the project owner requires - no React.FC, no deep nesting, early returns, plain CSS.
---

# React/TypeScript code style for this project

These rules are mandatory for every change under `frontend/`. They exist so the
code reads like a human wrote it.

## Component rules

- Never use `React.FC`, `FunctionComponent`, or the `FC` type. Write plain
  function components with an exported `Props` interface:

  ```tsx
  interface DocumentListProps {
    documents: DocumentInfo[];
    onRemove: (name: string) => void;
  }

  export function DocumentList({ documents, onRemove }: DocumentListProps) {
    // ...
  }
  ```

- One concern per component. If a component needs three unrelated chunks of
  state or markup, split it.
- Prefer early returns over nesting:

  ```tsx
  // Good
  if (documents.length === 0) {
    return <p>No documents yet.</p>;
  }

  return <ul>...</ul>;
  ```

  Do not write `documents.length === 0 ? <p/> : <ul/>` chains two levels deep,
  and never nest ternaries. An `if/else` statement in JSX-land (early return or
  a small helper) beats a clever expression every time.
- Maximum ~2 levels of nesting in JSX and in logic. Extract a subcomponent or
  a helper function instead.
- Name things after what they are in the domain (`session`, `documents`,
  `isUploading`), not after how they are implemented (`data1`, `stuff`,
  `handler2`).

## Data fetching rules

- Every API call goes through the reusable wrappers in `src/lib/http.ts`
  (`request<T>` for JSON, `uploadDocument` for multipart uploads). Never call
  `fetch` directly from a component or hook.
- Every call site wraps the await in `try/catch`. Map failures to user-facing
  messages; use the `ApiError.code` when the UI needs to branch (e.g.
  `unknown_session`).
- Requests are aborted with `AbortController`: one per chat send, aborted by
  the Stop button and on component unmount (`useEffect` cleanup).
- No request timeouts. The backend waits indefinitely for the LLM; the UI's
  only escape hatch is the abort button.
- Endpoint paths come from `src/constants/api.ts`. Never inline a raw path
  string like `"/chat"` in a hook.

## Hook rules

- Hooks expose named functions for the component to destructure - no action
  objects, no boolean soup:

  ```ts
  const { documents, uploadDocument, removeDocument, isUploading } = useSession();
  ```

- Keep hooks framework-agnostic and small. A hook that talks to more than one
  backend resource probably wants to be two hooks.

## Style rules

- Plain CSS in `src/styles/`. No Tailwind, no CSS-in-JS, no UI kits, no
  icon/font packages. Neutral palette (grays, near-black accents) - no blue
  gradients, no glow effects.
- No third-party runtime dependencies beyond `react` and `react-dom`.
- TypeScript strict mode stays on. No `any` unless interoperating with a
  genuinely untyped boundary (and then a `// eslint-disable`-style comment
  explaining why). Prefer `unknown` + narrowing.
- Default-export nothing except `main.tsx`. Named exports everywhere else.
