name = cw-hitch

srpm:
	sed -i "s/%global name[ \t].*/%global name\t\t$(name)/g" $(spec)
	mv $(spec) $(name).spec

	rpmbuild \
		-bs \
		--define "_srcrpmdir $(outdir)" \
		--define "_sourcedir $(CURDIR)" \
		--undefine "dist" \
		$(name).spec

