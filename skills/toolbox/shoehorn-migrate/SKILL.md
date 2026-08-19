---
name: shoehorn-migrate
description: Migrate test files from `as` type assertions to @total-typescript/shoehorn. Use when user mentions shoehorn, wants to replace `as` in tests, or needs partial test data.
---

# Shoehorn Migrate

`shoehorn` passes partial data into a test without lying to TypeScript about it — a type-safe stand-in for the `as` assertions tests tend to accumulate. **Test code only**; it has no place in production code.

`as` earns its bad reputation in tests for three reasons: agents are trained to avoid it, it makes you spell out the target type by hand, and faking wrong data on purpose degrades into a double-cast (`as unknown as Type`).

Install: `npm i @total-typescript/shoehorn`

## The three conversions

**A large type, only a few properties actually needed** — instead of faking all twenty fields on `Request` just to test `body.id`, wrap the partial object:

```ts
import { fromPartial } from "@total-typescript/shoehorn";

it("gets user by id", () => {
  getUser(fromPartial({ body: { id: "123" } }));
});
```

**`as Type` becomes `fromPartial()`** — same partial-data case, simpler starting point:

```ts
// before
getUser({ body: { id: "123" } } as Request);

// after
import { fromPartial } from "@total-typescript/shoehorn";
getUser(fromPartial({ body: { id: "123" } }));
```

**`as unknown as Type` becomes `fromAny()`** — for data that's wrong on purpose, testing an error path:

```ts
// before
getUser({ body: { id: 123 } } as unknown as Request);

// after
import { fromAny } from "@total-typescript/shoehorn";
getUser(fromAny({ body: { id: 123 } }));
```

| Function | Reach for it when |
| --- | --- |
| `fromPartial()` | the data is partial but should still type-check |
| `fromAny()` | the data is intentionally wrong, and you still want autocomplete while writing it |
| `fromExact()` | you want the full object enforced — a stepping stone before swapping in `fromPartial` |

## Doing the migration

Before touching anything, ask what's actually driving the request: which test files have problem `as` assertions, whether the pain is really about large objects with a few relevant fields, and whether any of it is intentionally-wrong data for error-path tests.

Then work through it: install the package; find candidates with `grep -r " as [A-Z]" --include="*.test.ts" --include="*.spec.ts"`; swap `as Type` for `fromPartial()` and `as unknown as Type` for `fromAny()`; add the new imports; run the type checker to confirm nothing's left dangling.
