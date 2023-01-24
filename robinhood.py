import asyncio
import aiohttp

from loguru import logger
from aiohttp import ClientSession
from random import choice, randint
from aiohttp_proxy import ProxyConnector
from pyuseragents import random as random_useragent


def random_tor_proxy():
    proxy_auth = str(randint(1, 0x7fffffff)) + ':' + \
        str(randint(1, 0x7fffffff))
    proxies = f'socks5://{proxy_auth}@localhost:' + str(choice([9150]))
    return(proxies)


async def get_connector():
    connector = ProxyConnector.from_url(random_tor_proxy())
    return(connector)


async def sending_captcha(client: ClientSession):
    try:
        response = await client.get(f'http://api.captcha.guru/in.php?key={user_key}&method=userrecaptcha \
            &googlekey=6LcNCM0fAAAAAJLML8tBF-AMvjkws6z4bfar9VFF&pageurl=https://robinhood.com/web3-wallet/&softguru=129939')
        data = await response.text()
        if 'ERROR' in data:
            logger.error(data)
            await asyncio.sleep(1)
            return(await sending_captcha(client))
        id = data[3:]
        return(await solving_captcha(client, id))
    except:
        raise Exception()


async def solving_captcha(client: ClientSession, id: str):
    for i in range(100):
        try:
            response = await client.get(f'http://api.captcha.guru/res.php?key={user_key}&action=get&id={id}')
            data = await response.text()
            if 'ERROR' in data:
                logger.error(data)
                raise Exception()
            elif 'OK' in data:
                return(data[3:])
            return(await solving_captcha(client, id))
        except:
            raise Exception()
    raise Exception()


async def create_email(client: ClientSession):
    try:
        response = await client.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        email = (await response.json())[0]
        return email
    except Exception:
        logger.error("Failed to create email")
        await asyncio.sleep(1)
        return await create_email(client)


async def worker():
    while True:
        try:
            async with aiohttp.ClientSession(
                connector=await get_connector(),
                headers={'user-agent': random_useragent()}
            ) as client:

                logger.info('Get email')
                email = await create_email(client)

                logger.info('Send email')
                response = await client.post('https://bonfire.robinhood.com/waitlist/web3_wallet/email/spot', 
                    json={
                      "email":email,
                      "token":await sending_captcha(client),
                      "referred_by":ref
                    })
                data = await response.text()
                if 'new' not in data:
                    logger.error(data)
                    raise Exception
        except:
            logger.exception('Error\n')
        else:
            with open('registered.txt', 'a', encoding='utf-8') as file:
                file.write(f'{email}\n')
            logger.success('Successfully\n')

        await asyncio.sleep(delay)


async def main():
    tasks = [asyncio.create_task(worker()) for _ in range(threads)]
    await asyncio.gather(*tasks)

    
if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("Bot Robinhood @flamingoat\n")

    user_key = input('Captcha key: ')
    ref = str(input('Referral code'))
    delay = int(input('Delay(sec): '))
    threads = int(input('Threads: '))

    asyncio.run(main())