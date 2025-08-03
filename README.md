### Input JSON Format:
```json
{
  "message": "How can I stay calm in difficult situations?",
  "history": [
    {
      "role": "user",
      "content": "<User past msg>"
    },
    {
      "role": "model",
      "content": "<API past response>"
    }
  ]
}
```
### Output JSON Format:
#### Successful Response
```json
{
  "status": "success",
  "matched_verse": {
    "chapter": <Chapter_no>,
    "verse": <Verse_no.>,
    "eng_meaning": "<Gita Verse>",
    "similarity": 0.86
  },
  "gemini_response": "<Gemini Respose>"
}
```
#### Error Responses
```json
{
  "error": "<Error Msg>"
}

```


    

