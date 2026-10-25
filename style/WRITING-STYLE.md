## Writing style

Write all responses and messages in simple, easy English. Aim for 80% of the way
to ASD-STE100, the controlled-language standard for aerospace maintenance
manuals. The standard is too strict to follow in full. Apply these rules:

1. **Use short sentences.** One idea per sentence. Keep most sentences under 20
   words.
2. **Use the active voice.** Write "the test failed", not "the test was failed by
   the run".
3. **Give one instruction per sentence.** Do not join two actions with "and".
4. **Use simple present tense.** Write "the server returns 409", not "the server
   will be returning 409".
5. **Use common words.** Choose the short, plain word. Write "use", not
   "utilise". Write "start", not "commence". Write "help", not "facilitate".
6. **Do not stack nouns.** Write "the value of the cell", not "the cell value
   field container".
7. **Keep one name for one thing.** If a thing is a "slice", always call it a
   "slice". Do not switch to "task", "ticket" or "item".
8. **Keep the articles.** Write "open the file", not "open file".
9. **Cut filler.** Remove "just", "actually", "simply", "basically",
   "essentially", "it is worth noting that", and "in order to" (write "to").
10. **Do not use idioms or metaphors.** Say the plain fact.

Never change these to fit the style:

- Code, file paths, commands, identifiers, and error codes. Keep them exact.
- Quoted output, test names, and spec quotes.
- Technical terms that have no simpler replacement. Explain the term once, then
  reuse it.

The style applies to prose. It does not apply to code, tables of data, commands,
quoted output, or the receipt block.

### Priority

This style sets the minimum. A terse mode such as `trim-my-output` (caveman) may
cut further, and may not cut below this minimum. Always keep the articles, one
name for each thing, and one instruction per sentence.
