"""Run the application on a fixed loopback listener without raw URL access logs."""

import uvicorn


def main():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, access_log=False, proxy_headers=False)


if __name__ == "__main__":
    main()
