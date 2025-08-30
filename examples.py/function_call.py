import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
apikey = os.getenv("OPENAI_COMPATIBLE_APIKEY")
client = OpenAI(api_key=apikey, base_url="http://localhost:3648/v1")

tools = [
    {
        "type": "function",
        "name": "book_restaurant_reservation",
        "description": "Book a restaurant reservation.",
        "parameters": {
            "type": "object",
            "properties": {
                "restaurant": {"type": "string", "description": "Restaurant name"},
                "date_time": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Reservation date and time",
                },
                "party_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Number of people",
                },
            },
            "required": ["restaurant", "date_time", "party_size"],
            "additionalProperties": False,
        },
    }
]

stream = True
# Simplified example for a reservation
reservation_response = client.chat.completions.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "帮我预定一个三人餐，明天晚上7点， 新荣记, 其他信息你随便填。"}],
    tools=tools,
    stream=stream,
)

# Output the reservation response
if stream:

    for event in reservation_response:
                if event.choices:

                    if event.choices[0].delta:
                        content_delta = event.choices[0].delta
                        print(content_delta)
                        # print(event.choices[0].message.content)
                        print("\n")
else:
    # if event.choices[0].message.content:
    #     print(event.choices[0].message.content)
    #     print("\n")
    print(reservation_response)
