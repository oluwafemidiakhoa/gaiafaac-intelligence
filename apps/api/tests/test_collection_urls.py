from gaiafaac_api.pipeline.collection.oagf_urls import candidate_urls


def test_january_2024_matches_verified_real_url():
    urls = candidate_urls(2024, 1)
    assert urls[0] == (
        "https://oagf.gov.ng/wp-content/uploads/2024/02/Disbursement-January-2024.pdf"
    )
    # fallback tries the following publication month too
    assert urls[1] == (
        "https://oagf.gov.ng/wp-content/uploads/2024/03/Disbursement-January-2024.pdf"
    )


def test_december_rolls_publication_year_forward():
    urls = candidate_urls(2024, 12)
    assert urls[0] == (
        "https://oagf.gov.ng/wp-content/uploads/2025/01/Disbursement-December-2024.pdf"
    )


def test_tries_up_to_four_month_publication_lag():
    # OAGF has filed as late as +4 months (Dec 2024 -> 2025/04); discovery must reach it.
    urls = candidate_urls(2024, 12)
    assert len(urls) == 4
    assert urls[3] == (
        "https://oagf.gov.ng/wp-content/uploads/2025/04/Disbursement-December-2024.pdf"
    )
