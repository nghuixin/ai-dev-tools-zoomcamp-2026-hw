import { expect, test } from '@playwright/test'

/**
 * Two-session E2E against docker-compose.yml.
 *
 * This app has no accounts or interview rooms. Session 1 / session 2 are
 * isolated browser contexts (interviewer / candidate). The join link is
 * /?board=<id>. There is no live sync; the interviewer reloads to see Postgres.
 */
test('candidate canvas change appears for the interviewer', async ({ browser }) => {
  const interviewer = await browser.newContext()
  const candidate = await browser.newContext()
  const session1 = await interviewer.newPage()
  const session2 = await candidate.newPage()
  const room = `Interview ${Date.now()}`

  await session1.goto('/')
  await expect(session1.getByText('Loading board…')).toHaveCount(0)
  await expect(session1.getByRole('textbox', { name: 'Board name', exact: true })).toBeVisible()
  await session1.getByLabel('New board name').fill(room)
  await session1.getByRole('button', { name: 'Create' }).click()
  await expect(session1.getByRole('textbox', { name: 'Board name', exact: true })).toHaveValue(
    room,
  )
  await expect(session1.getByRole('button', { name: 'Copy join link' })).toBeVisible()
  await expect(session1).toHaveURL(/[?&]board=/)

  const joinLink = session1.url()

  await session2.goto(joinLink)
  await expect(session2.getByText('Loading board…')).toHaveCount(0)
  await expect(session2.getByRole('textbox', { name: 'Board name', exact: true })).toHaveValue(
    room,
  )

  await session2.getByLabel('Add card to To Do').fill('Candidate changed the canvas')
  await session2.getByLabel('Add card to To Do').press('Enter')
  await expect(
    session2.getByRole('heading', { name: 'Candidate changed the canvas' }),
  ).toBeVisible()

  await session1.reload()
  await expect(session1.getByText('Loading board…')).toHaveCount(0)
  await expect(session1.getByRole('textbox', { name: 'Board name', exact: true })).toHaveValue(
    room,
  )
  await expect(
    session1.getByRole('heading', { name: 'Candidate changed the canvas' }),
  ).toBeVisible()

  await interviewer.close()
  await candidate.close()
})
