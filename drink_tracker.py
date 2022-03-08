def handler(event, context):
    print("Received event: " + str(event))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response><Message><Body>Hello world! -Lambda</Body><Media>https://demo.twilio.com/owl.png</Media></Message></Response>"
    )
