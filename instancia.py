class Instancia:
    def __init__(self,T,q,W,L,R,C,Q,l=None,IFP=None,NFP=None):
        # ISSP
        self.T=T
        self.q=q
        self.W=W
        self.L=L
        self.R=R
        self.C=C
        # BPP
        self.Q=Q
        self.l=l
        # ISSP tbm (só depende de W,L,R,C,T)
        self.IFP=IFP
        self.NFP=NFP
