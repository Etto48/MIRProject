<!-- module: mir.ir.token_ir -->

## Tokens
Now we defines structures to manage and classify tokens within a document or query.

- `TokenLocation`: An enumeration (Enum) that specifies the possible locations of a token, including QUERY, AUTHOR, TITLE, and BODY.

- `Token`: A data class (@dataclass) representing a token with two attributes:

	- `text`: The token's string value.
	- `location`: A TokenLocation enum instance that indicates where the token is located (e.g., in the query, author field, title, or body).