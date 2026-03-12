import subprocess
import logging
from common.decorators import log_time, safe

logger = logging.getLogger('contactmailer')

@safe
@log_time
def check_smtp_host(host: str) -> bool:
    """
    Pings the SMTP host to check connectivity using the subprocess module.
    Returns True if reachable, False otherwise.
    """
    logger.info(f"Checking connectivity to SMTP host: {host}")
    # using ping -c 1 for linux/mac. For windows it would be ping -n 1
    # We will assume a unix-like environment but fallback gracefully if it fails.
    try:
        # ping command: -c 1 means send 1 packet. -W 2 means 2 seconds timeout.
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        logger.info(f"Ping successful for {host}:\n{result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Ping failed for {host}. Exit code: {e.returncode}\n{e.stderr.strip()}")
        return False
    except FileNotFoundError:
        # If ping is not found, we can try nslookup
        logger.warning("ping command not found. Trying nslookup instead.")
        try:
            result = subprocess.run(
                ['nslookup', host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            logger.info(f"nslookup successful for {host}:\n{result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"nslookup failed for {host}.\n{e.stderr.strip()}")
            return False
