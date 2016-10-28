// local size 0 + 4/8 (32bit/64bit)
long func_omega(void) {
	return 0;
}

// local size 0 + 4/8 (32bit/64bit)
long func_alpha(long a) {
	return a + 1;
}

// local size 32 + 4/8 (32bit/64bit)
long func_beta(long a, long b) {
	long tmp = a + b;

	tmp = func_alpha(tmp);
	
	return tmp;
}

// local size 40 + 4/8 (32bit/64bit)
long func_gamma(long a, long b, long c) {
	long tmp = 0;

	tmp = func_alpha(tmp);
	tmp = func_beta(tmp, a);

	return tmp + a + b + c;
}

// local size 48 + 4/8 (32bit/64bit)
long func_delta(long a, long b, long c, long d) {
	long tmp = 0;

	tmp += func_alpha(a);
	tmp += func_beta(a, b);
	tmp += func_gamma(a, b, c);

	return tmp + a + b + c + d;
}

// local size 56 + 4/8 (32bit/64bit)
long func_epsilon(long a, long b, long c, long d, long e) {
	long tmp = 0;

	tmp += func_alpha(a);
	tmp += func_beta(a, b);
	tmp += func_gamma(a, b, c);
	tmp += func_delta(a, b, c, d);

	return tmp + a + b + c + d + e;
}

// local size 64 + 4/8 (32bit/64bit)
long func_zeta(long a, long b, long c, long d, long e, long f) {
	long tmp = 0;
	long temp = 0;

	tmp += func_alpha(a);
	tmp += func_beta(a, b);
	tmp += func_gamma(a, b, c);
	tmp += func_delta(a, b, c, d);
	temp += func_epsilon(a, b, c, d, e);

	return tmp + temp + a + b + c + d + e + f;
}

// local size 16 + 4/8 (32bit/64bit)
long rec_xi(long a) {
	if (a < 10) {
		a++;
	}

	return rec_xi(a);
}

long rec_psi(long a);

// local size 16 + 4/8 (32bit/64bit)
long rec_phi(long a) {
	if (a < 10) {
		return rec_psi(a + 1);
	}

	return a;
}

// local size 16 + 4/8 (32bit/64bit)
long rec_chi(long a) {
	return rec_phi(a + 1);
}

// local size 16 + 4/8 (32bit/64bit)
long rec_psi(long a) {
	return rec_chi(a + 1);
}

// local size 32 + 4/8 (32bit/64bit)
long main(long argc, long** argv) {
	long a;
	long (*fp)(long a);

	a = func_omega();
	a = func_zeta(a, a, a, a, a, a);
	a = rec_psi(a);

	if (a < 10) {
		fp = &rec_phi;
	} else {
		fp = &func_alpha;
	}

	a = fp(a);
	a += rec_xi(a);
	a += rec_xi(a);

	return a + 1;
}
