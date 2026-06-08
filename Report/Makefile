LATEXMK = latexmk
LATEXFLAGS = -pdf -interaction=nonstopmode -halt-on-error

REPORT = Main-Report.tex
THESIS = Main-Thesis.tex

.PHONY: all report thesis all-clean report-clean thesis-clean clean clean-all

all: report thesis

report:
	$(LATEXMK) $(LATEXFLAGS) $(REPORT)

thesis:
	$(LATEXMK) $(LATEXFLAGS) $(THESIS)

report-clean:
	$(LATEXMK) $(LATEXFLAGS) $(REPORT)
	$(LATEXMK) -c $(REPORT)
	rm -f Main-Report.aux Main-Report.bbl Main-Report.blg Main-Report.bcf Main-Report.fdb_latexmk Main-Report.fls Main-Report.lof Main-Report.log Main-Report.lot Main-Report.out Main-Report.run.xml Main-Report.synctex.gz Main-Report.toc Main-Report-blx.bib
	rm -f chapter/*.aux

thesis-clean:
	$(LATEXMK) $(LATEXFLAGS) $(THESIS)
	$(LATEXMK) -c $(THESIS)
	rm -f Main-Thesis.aux Main-Thesis.bbl Main-Thesis.blg Main-Thesis.bcf Main-Thesis.fdb_latexmk Main-Thesis.fls Main-Thesis.lof Main-Thesis.log Main-Thesis.lot Main-Thesis.out Main-Thesis.run.xml Main-Thesis.synctex.gz Main-Thesis.toc Main-Thesis-blx.bib
	rm -f chapter/*.aux

all-clean: report-clean thesis-clean

clean:
	$(LATEXMK) -c $(REPORT)
	$(LATEXMK) -c $(THESIS)
	rm -f Main-Report.aux Main-Report.bbl Main-Report.blg Main-Report.bcf Main-Report.fdb_latexmk Main-Report.fls Main-Report.lof Main-Report.log Main-Report.lot Main-Report.out Main-Report.run.xml Main-Report.synctex.gz Main-Report.toc Main-Report-blx.bib
	rm -f Main-Thesis.aux Main-Thesis.bbl Main-Thesis.blg Main-Thesis.bcf Main-Thesis.fdb_latexmk Main-Thesis.fls Main-Thesis.lof Main-Thesis.log Main-Thesis.lot Main-Thesis.out Main-Thesis.run.xml Main-Thesis.synctex.gz Main-Thesis.toc Main-Thesis-blx.bib
	rm -f chapter/*.aux

clean-all:
	$(LATEXMK) -C $(REPORT)
	$(LATEXMK) -C $(THESIS)
