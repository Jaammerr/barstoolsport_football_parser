import asyncio
import json

from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    ElementHandle,
    Browser,
    Playwright
)
from bs4 import BeautifulSoup
from playwright_stealth import stealth_async
from loguru import logger

from .models import *
from .errors import ParserError



class Parser:
    def __init__(self, timeout: int, proxy: str = None):
        self.main_url: str = "https://barstoolsportsbook.com"
        self.timeout: int = timeout
        self.proxy: str = proxy

        self.playwright: Playwright = None  # type: ignore
        self.browser: Browser = None  # type: ignore
        self.page: Page = None  # type: ignore

    async def setup_browser(self) -> None:
        try:
            self.playwright = await async_playwright().start()
            if self.proxy:
                ip, port, user, password = self.proxy.split(":")
                self.browser = await self.playwright.chromium.launch(
                    headless=False,
                    proxy={
                        "server": f"http://{ip}:{port}",
                        "username": user,
                        "password": password,
                    },
                )
            else:
                self.browser = await self.playwright.chromium.launch(headless=False)

            self.page = await self.browser.new_page()
            # Stealth mode for bypassing the bot protection if it is enabled
            await stealth_async(self.page)
            await self.page.goto(self.main_url, wait_until="load", timeout=60000)

        except Exception as error:
            raise ParserError(f"Error while setting up browser: {error}")

    async def get_additional_bets(
        self,
        league_events_list: list[FootballLeagueEventsList],
        all_lines_button_selector: str = "button.flex.cursor-pointer.select-none.items-center",
    ) -> list[FootballLeagueEventsList]:
        for league_events in league_events_list:
            for event in league_events.events:
                logger.info(f"Getting additional bets for event: {event.id}..")
                url = f"{self.main_url}/sport/football/organization/united-states/competition/{league_events.leagueName.lower()}/event/{event.id}"

                try:
                    await self.page.goto(url, wait_until="load")
                    # If the url is incorrect, then the page will be redirected to the main page
                    if self.page.url != url:
                        continue

                    await self.page.wait_for_selector(all_lines_button_selector)
                    lines_selectors = await self.page.locator(
                        all_lines_button_selector
                    ).all()

                except PlaywrightTimeoutError:
                    logger.error(
                        f"Error while getting additional bets for event: {event.id} | Skipping.."
                    )
                    continue

                match_spreads_team1 = []
                match_spreads_team2 = []
                total_points_team1 = []
                total_points_team2 = []

                for index, line in enumerate(lines_selectors):
                    try:
                        await line.click(timeout=2000)
                    except PlaywrightTimeoutError:
                        ...

                    await asyncio.sleep(2)  # waiting while modal dialog will be opened
                    soup = BeautifulSoup(await self.page.content(), "html.parser")
                    elements = soup.find_all(
                        "div", {"class": "bg-card-primary flex flex-col gap-4"}
                    )

                    if not elements:
                        logger.error(
                            f"Error while getting additional bets for event: {event.id} | Skipping.."
                        )
                        continue

                    # Index 1 because the first element is the main bet
                    for el in elements[1]:
                        teams = el.find_all(
                            "span",
                            {"class": "font-medium text-selector-label-deselected"},
                        )
                        teams1, teams2 = (team.text for team in teams)

                        money = el.find_all("span", {"class": "font-bold"})
                        money1, money2 = (m.text for m in money)

                        if index == 0:
                            match_spreads_team1.append(
                                FootballMatchSpread(spread=teams1, moneyline=money1)
                            )
                            match_spreads_team2.append(
                                FootballMatchSpread(spread=teams2, moneyline=money2)
                            )
                        else:
                            total_points_team1.append(
                                FootballTotalPoints(total=teams1, moneyline=money1)
                            )
                            total_points_team2.append(
                                FootballTotalPoints(total=teams2, moneyline=money2)
                            )

                    try:
                        await self.page.click(
                            "button[aria-label='Close']", timeout=2000
                        )
                    except PlaywrightTimeoutError:
                        # Break because the modal dialog is not closed and the page is not updated to open the next dialog
                        break

                event.teams[0].match_spreads = match_spreads_team1
                event.teams[0].total_points = total_points_team1
                event.teams[1].match_spreads = match_spreads_team2
                event.teams[1].total_points = total_points_team2

        return league_events_list

    async def close_modal(
        self, close_button_selector: str = "button[data-testid='modal-close-button']"
    ) -> None:
        # Close modal dialog if it is opened when the page is loaded
        try:
            modal = await self.page.wait_for_selector(
                close_button_selector, timeout=3000
            )
            await modal.click()

        except PlaywrightTimeoutError:
            return

    async def get_available_leagues(
        self,
        football_button_selector: str = "#__next > div > div.z-0.flex.min-h-full.flex-col.flex-nowrap > main > div:nth-child(1) > div > nav > ul > li:nth-child(21)",
        leagues_list_selector: str = "li[data-testid='sport-menu-item']",
    ) -> list[ElementHandle]:
        try:
            # Getting main page second time because we are using "while True" loop
            await self.page.goto(self.main_url, wait_until="load")
            football_button = await self.page.wait_for_selector(
                football_button_selector, timeout=5000
            )
            await football_button.click()

            handles = await self.page.query_selector_all(leagues_list_selector)
            return handles

        except PlaywrightTimeoutError:
            raise ParserError("Football leagues list not found")

    async def get_league_events(
        self,
        league: ElementHandle,
        marketplace_shelf_selector: str = "div[data-testid='marketplace-shelf-']",
        events_selector: str = ".bg-card-primary.rounded.p-4",
    ) -> FootballLeagueEventsList:
        await league.click()

        league_name: str = await league.text_content()
        marketplace_shelf = await self.page.wait_for_selector(
            marketplace_shelf_selector, timeout=5000
        )
        if not marketplace_shelf:
            raise ParserError("Marketplace shelf not found (league events list)")

        events = await marketplace_shelf.query_selector_all(events_selector)
        league_events = []

        for event in events:
            try:
                # Getting event ID for ability to parse additional bets
                event_id = (await event.get_attribute("id")).split("|")[1]
                soup = BeautifulSoup(await event.inner_html(), "html.parser")

                startDate = soup.find("span", {"class": "mr-2"}).text

                commands = soup.find_all(
                    "div", {"class": "text-primary text-description text-primary"}
                )
                command1, command2 = (command.text for command in commands)

                scores = soup.find_all(
                    "div", {"class": "text-subdued-primary mt-0.5 text-footnote"}
                )
                score1, score2 = (score.text for score in scores)

                bets = soup.find_all(
                    "div", {"class": "flex items-center gap-2 pt-2 w-[53%]"}
                )
                spread1, total1, moneyline1 = (bet.text for bet in bets[0])
                spread2, total2, moneyline2 = (bet.text for bet in bets[1])

                league_events.append(
                    FootballEventData(
                        id=event_id,
                        startDate=startDate,
                        teams=[
                            FootballTeamData(
                                name=command1,
                                score=score1,
                                spread=spread1,
                                total=total1,
                                moneyline=moneyline1,
                            ),
                            FootballTeamData(
                                name=command2,
                                score=score2,
                                spread=spread2,
                                total=total2,
                                moneyline=moneyline2,
                            ),
                        ],
                    )
                )

            except Exception as error:
                logger.error(f"Error while parsing event data: {error}")

        if not league_events:
            raise ParserError("League events not found")

        return FootballLeagueEventsList(leagueName=league_name, events=league_events)

    @staticmethod
    def export_events_to_json(
        output_file: str, league_events: list[FootballLeagueEventsList]
    ) -> None:
        export_data = {}

        for league in league_events:
            export_data[league.leagueName] = league.model_dump()

        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(export_data, json_file, ensure_ascii=False, indent=4)

    async def start(self) -> None:
        try:
            await self.setup_browser()
        except ParserError as error:
            logger.error(f"Error while setting up browser: {error}")
            return

        logger.info("Closing modal dialog..")
        await self.close_modal()

        while True:
            try:
                logger.info("Getting available leagues..")
                leagues_handles = await self.get_available_leagues()

                logger.info("Getting events for each league..")
                total_events = [
                    await self.get_league_events(league_handle)
                    for league_handle in leagues_handles
                ]

                logger.info("Getting additional bets for each league events..")
                await self.get_additional_bets(total_events)

                self.export_events_to_json("output.json", total_events)
                logger.success("Events exported to output.json\n")

                await asyncio.sleep(self.timeout)

            except (ParserError, Exception) as error:
                logger.error(f"Error while parsing: {error}")
                await self.browser.close()
                await self.playwright.stop()

                break
