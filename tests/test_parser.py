from parser import Parser


def test_parser():
    parser = Parser('https://www.billboard.com/charts/hot-100/2000-01-02/')

    if (data := parser.parse(parser.get())):
        assert data[1]['title'] == 'Back At One'
        assert data[2]['artist'] == 'Jessica Simpson'
