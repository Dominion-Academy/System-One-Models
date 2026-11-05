from typesafe_sdk import Choice, Noul

CATEGORY = Choice(
    instructions="Which kind of problem is described in the support ticket",
    criteria={
        "billing": "Payments, invoices, refunds, subscription charges",
        "technical": "Bugs, errors, API or integration problems",
        "account": "Login, password, profile and account settings",
        "other": "Anything else: feature requests, general questions, feedback",
    },
)

URGENT = Noul(
    instructions="The customer cannot work or loses money right now and needs a quick answer",
    criteria={
        "true": "A blocking problem or a hard deadline, the customer needs help immediately",
        "false": "No blocker and no deadline, the request can wait",
    },
)
