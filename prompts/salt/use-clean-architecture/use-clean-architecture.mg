<<
## Clean architecture:

We should structure our code in a way where dependencies point inwards, towards higher-level policies.
This means that the core business logic should not depend on external frameworks, databases, or user interfaces.
Instead, these external components should depend on the core logic.

Layers:
- App: This layer contains the application-specific logic usually the web application code only or cli only.
- Core: This layer contains the business rules and logic. It is independent of any external systems. We use interfaces to talk with concrete implementations in outer layers.
- Entities: This layer contains the enterprise-wide business rules. It encapsulates the most general and high-level rules.
- Libs: This layer contains shared libraries and utilities that can be used across different parts of the application.

We should use dependency inversion to ensure that high-level modules do not depend on low-level modules.
Both should depend on abstractions (e.g., interfaces).
This allows us to change the implementation details without affecting the core business logic.
>>