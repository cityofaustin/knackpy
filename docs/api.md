# Knackpy API Reference

To understand knackpy's design, it's helpful to think of it in terms of two entry points:

- [`Api`](./api): Contains core functions for over-the-wire interactions with the Knack API, as well as helpers for pagination and re-trying on request failures.
- [`App`](./app): The highest-level container for getting and interacting with Knack records.

The other the knackpy classes act as a hierarchy that are constructed through a chain of side-effects originating from  `App` objects.

- [`Record`](./record): A [dict-like](https://docs.python.org/3/library/collections.abc.html) container for `Field` objects which supplies helpers for accesing and formatting fields.
- [`Field`](./fields#field-objects): A container for a single Knack key/value, with helpers for formatting.
- [`FieldDef`](./fields#fielddef-objects): Stores field metadata (type, formatting method, parent objects/views)
