from pyflink.common.typeinfo import Types

# Example Object
# {\"user_id\": \"424cdd21-063a-43a7-b91b-7ca1a833afae\", \"app_version\": \"2.3.0\",
# \"device_type\": \"android\", \"ip\": \"199.172.111.135\", \"locale\": \"RU\", \"device_id\":
# \"593-47-5928\", \"timestamp\":\"1694479551\"}

USER_LOGIN_SCHEMA = Types.ROW_NAMED(
    [
        "user_id",
        "app_version",
        "device_type",
        "ip",
        "locale",
        "device_id",
        "timestamp"
    ],
    [
        Types.STRING(),
        Types.STRING(),
        Types.STRING(),
        Types.STRING(),
        Types.STRING(),
        Types.STRING(),
        Types.STRING(),
    ]
)
