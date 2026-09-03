import os
os.makedirs('src/utils', exist_ok=True)
path = 'src/utils/config.py'
with open(path, 'w') as f:
    f.write('import os\\n')
    f.write('from pydantic import BaseModel\\n')
    f.write('from pydantic_settings import BaseSettings\\n\\n')
    f.write('class DatabaseConfig(BaseModel):\\n')
    f.write('    host = \
localhost\\\n')
    f.write('    port = 5432\\n')
    f.write('    name = \
predixa\\\n')
    f.write('    user = \
postgres\\\n')
    f.write('    password = \
\\\n')
    f.write('    pool_size = 10\\n')
    f.write('    max_overflow = 20\\n\\n')
    f.write('    @property\\n')
    f.write('    def url(self):\\n')
    f.write('        return \
postgresql://\ + self.user + \:\ + self.password + \@\ + self.host + \:\ + str(self.port) + \/\ + self.name\\n\\n')
    f.write('    @property\\n')
    f.write('    def async_url(self):\\n')
    f.write('        return \
postgresql+asyncpg://\ + self.user + \:\ + self.password + \@\ + self.host + \:\ + str(self.port) + \/\ + self.name\\n\\n')
    f.write('class RedisConfig(BaseModel):\\n')
    f.write('    host = \
localhost\\\n')
    f.write('    port = 6379\\n')
    f.write('    db = 0\\n')
    f.write('    password = \
\\\n\\n')
    f.write('    @property\\n')
    f.write('    def url(self):\\n')
    f.write('        if self.password:\\n')
    f.write('            return \
redis://:\ + self.password + \@\ + self.host + \:\ + str(self.port) + \/\ + str(self.db)\\n')
    f.write('        return \
redis://\ + self.host + \:\ + str(self.port) + \/\ + str(self.db)\\n\\n')
    f.write('class Settings(BaseSettings):\\n')
    f.write('    app_name = \
predixa-ai\\\n')
    f.write('    app_version = \
0.1.0\\\n')
    f.write('    environment = \
development\\\n')
    f.write('    database = DatabaseConfig()\\n')
    f.write('    redis = RedisConfig()\\n\\n')
    f.write('    class Config:\\n')
\\\n')
    f.write('        env_nested_delimiter = \
__\\\n\\n')
    f.write('settings = Settings()\\n\\n')
    f.write('def get_config():\\n')
    f.write('    return settings\\n')
