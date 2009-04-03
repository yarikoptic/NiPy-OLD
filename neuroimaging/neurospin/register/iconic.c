#include "iconic.h"
#include "cubic_spline.h"

#include <randomkit.h>

#include <math.h>
#include <stdlib.h>
#include <string.h>


#define SQR(a) ((a)*(a))
#define FLOOR(a)((a)>0.0 ? (int)(a):(((int)(a)-a)!= 0.0 ? (int)(a)-1 : (int)(a)))  
#define UROUND(a) ((int)(a+0.5))


static double _marginalize(double* h, const double* H, int clampI, int clampJ, int axis); 
static void _L1_moments (const double * h, int clamp, int stride, double* median, double* dev, double* sumh);

static inline void _apply_affine_transform(double* Tx, double* Ty, double* Tz, 
					   const double* Tvox, size_t x, size_t y, size_t z); 

static inline void _pv_interpolation(int i, 
				     double* H, int clampJ, 
				     const signed short* J, 
				     const double* W, 
				     int nn, 
				     void* params);

static inline void _tri_interpolation(int i, 
				      double* H, int clampJ, 
				      const signed short* J, 
				      const double* W, 
				      int nn, 
				      void* params);

static inline void _rand_interpolation(int i, 
				       double* H, int clampJ, 
				       const signed short* J, 
				       const double* W, 
				       int nn, 
				       void* params); 



/* Numpy import */
void iconic_import_array(void) { 
  import_array(); 
  return;
}


/* =========================================================================
   JOINT HISTOGRAM COMPUTATION 
   ========================================================================= */

/*
  
iterI : assumed to iterate over a signed short encoded, possibly non-contiguous array.

imJ_padded : assumed C-contiguous (last index varies faster) & signed
short encoded.

H : assumed C-contiguous 

Tvox : assumed C-contiguous

Negative intensities are ignored. 

*/

#define APPEND_NEIGHBOR(q, w)			\
  j = J[q];					\
  if (j>=0) {					\
    *bufJnn = j; bufJnn ++; 			\
    *bufW = w; bufW ++;				\
    nn ++; }


void joint_histogram(double* H, 
		     int clampI, 
		     int clampJ,  
		     PyArrayIterObject* iterI,
		     const PyArrayObject* imJ_padded, 
		     const double* Tvox, 
		     int interp)
{
  const signed short* J=(signed short*)imJ_padded->data; 
  size_t dimJX=imJ_padded->dimensions[0]-2, dimJY=imJ_padded->dimensions[1]-2, dimJZ=imJ_padded->dimensions[2]-2;  
  signed short Jnn[8]; 
  double W[8]; 
  signed short *bufI, *bufJnn; 
  double *bufW; 
  int i, j;
  size_t off;
  size_t u2 = imJ_padded->dimensions[2]; 
  size_t u3 = u2+1; 
  size_t u4 = imJ_padded->dimensions[1]*u2;
  size_t u5 = u4+1; 
  size_t u6 = u4+u2; 
  size_t u7 = u6+1; 
  double wx, wy, wz, wxwy, wxwz, wywz; 
  double W0, W2, W3, W4; 
  size_t x, y, z; 
  int nn, nx, ny, nz;
  double Tx, Ty, Tz; 
  void (*interpolate)(int, double*, int, const signed short*, const double*, int, void*); 
  void* interp_params = NULL; 
  rk_state rng; 

  /* Reset the source image iterator */
  PyArray_ITER_RESET(iterI);

  /* Set interpolation method */ 
  if (interp==0) 
    interpolate = &_pv_interpolation;
  else if (interp>0) 
    interpolate = &_tri_interpolation; 
  else { /* interp < 0 */ 
    interpolate = &_rand_interpolation;
    rk_seed(-interp, &rng); 
    interp_params = (void*)(&rng); 
  }

  /* Re-initialize joint histogram */ 
  memset((void*)H, 0, clampI*clampJ*sizeof(double));

  /* Looop over source voxels */
  while(iterI->index < iterI->size) {
  
    /* Source voxel intensity */
    bufI = (signed short*)PyArray_ITER_DATA(iterI); 
    i = (int)bufI[0];

    /* Source voxel coordinates */
    x = iterI->coordinates[0];
    y = iterI->coordinates[1];
    z = iterI->coordinates[2];
    
    /* Compute the transformed grid coordinates of current voxel */ 
    _apply_affine_transform(&Tx, &Ty, &Tz, Tvox, x, y, z); 
    
    /* Test whether the current voxel is below the intensity
       threshold, or the transformed point is completly outside
       the reference grid */
    if ((i>=0) && 
	(Tx>-1) && (Tx<dimJX) && 
	(Ty>-1) && (Ty<dimJY) && 
	(Tz>-1) && (Tz<dimJZ)) {
	
      /* 
	 Nearest neighbor (floor coordinates in the padded
	 image, hence +1). 
	 
	 Notice that using the floor function doubles excetution time.
	 
	 FIXME: see if we can replace this with assembler instructions. 
      */
      nx = FLOOR(Tx) + 1;
      ny = FLOOR(Ty) + 1;
      nz = FLOOR(Tz) + 1;
      
      /* The convention for neighbor indexing is as follows:
       *
       *   Floor slice        Ceil slice
       *
       *     2----6             3----7                     y          
       *     |    |             |    |                     ^ 
       *     |    |             |    |                     |
       *     0----4             1----5                     ---> x
       */
      
      /*** Trilinear interpolation weights.  
	   Note: wx = nnx + 1 - Tx, where nnx is the location in
	   the NON-PADDED grid */ 
      wx = nx - Tx; 
      wy = ny - Ty;
      wz = nz - Tz;
      wxwy = wx*wy;    
      wxwz = wx*wz;
      wywz = wy*wz;
      
      /*** Prepare buffers */ 
      bufJnn = Jnn;
      bufW = W; 
      
      /*** Initialize neighbor list */
      off = nx*u4 + ny*u2 + nz; 
      nn = 0; 
      
      /*** Neighbor 0: (0,0,0) */ 
      W0 = wxwy*wz; 
      APPEND_NEIGHBOR(off, W0); 
      
      /*** Neighbor 1: (0,0,1) */ 
      APPEND_NEIGHBOR(off+1, wxwy-W0);
      
      /*** Neighbor 2: (0,1,0) */ 
      W2 = wxwz-W0; 
      APPEND_NEIGHBOR(off+u2, W2);  
      
      /*** Neightbor 3: (0,1,1) */
      W3 = wx-wxwy-W2;  
      APPEND_NEIGHBOR(off+u3, W3);  
      
      /*** Neighbor 4: (1,0,0) */
      W4 = wywz-W0;  
      APPEND_NEIGHBOR(off+u4, W4); 
      
      /*** Neighbor 5: (1,0,1) */ 
      APPEND_NEIGHBOR(off+u5, wy-wxwy-W4);   
      
      /*** Neighbor 6: (1,1,0) */ 
      APPEND_NEIGHBOR(off+u6, wz-wxwz-W4);  
      
      /*** Neighbor 7: (1,1,1) */ 
      APPEND_NEIGHBOR(off+u7, 1-W3-wy-wz+wywz);  
      
      /* Update the joint histogram using the desired interpolation technique */ 
      interpolate(i, H, clampJ, Jnn, W, nn, interp_params); 
      
      
    } /* End of IF TRANSFORMS INSIDE */
    
    /* Update source index */ 
    PyArray_ITER_NEXT(iterI); 
    
  } /* End of loop over voxels */ 
  

  return; 
}


/* Partial Volume interpolation. See Maes et al, IEEE TMI, 2007. */ 
static inline void _pv_interpolation(int i, 
				     double* H, int clampJ, 
				     const signed short* J, 
				     const double* W, 
				     int nn, 
				     void* params) 
{ 
  int k;
  int clampJ_i = clampJ*i;
  const signed short *bufJ = J;
  const double *bufW = W; 

  for(k=0; k<nn; k++, bufJ++, bufW++) 
    H[*bufJ+clampJ_i] += *bufW;
 
  return; 
}

/* Trilinear interpolation. Basic version. */
static inline void _tri_interpolation(int i, 
				      double* H, int clampJ, 
				      const signed short* J, 
				      const double* W, 
				      int nn, 
				      void* params) 
{ 
  int k;
  int clampJ_i = clampJ*i;
  const signed short *bufJ = J;
  const double *bufW = W; 
  double jm, sumW; 
  
  for(k=0, sumW=0.0, jm=0.0; k<nn; k++, bufJ++, bufW++) {
    sumW += *bufW; 
    jm += (*bufW)*(*bufJ); 
  }
  if (sumW > 0.0) {
    jm /= sumW;
    H[UROUND(jm)+clampJ_i] += 1;
  }
  return; 
}

/* Random interpolation. */
static inline void _rand_interpolation(int i, 
				       double* H, int clampJ, 
				       const signed short* J, 
				       const double* W, 
				       int nn, 
				       void* params) 
{ 
  rk_state* rng = (rk_state*)params; 
  int k;
  int clampJ_i = clampJ*i;
  const double *bufW;
  double sumW, draw; 
  
  for(k=0, bufW=W, sumW=0.0; k<nn; k++, bufW++) 
    sumW += *bufW; 
  
  draw = sumW*rk_double(rng); 

  for(k=0, bufW=W, sumW=0.0; k<nn; k++, bufW++) {
    sumW += *bufW; 
    if (sumW > draw) 
      break; 
  }
    
  H[J[k]+clampJ_i] += 1;
  
  return; 
}



static inline void _apply_affine_transform(double* Tx, double* Ty, double* Tz, 
					   const double* Tvox, size_t x, size_t y, size_t z)
{
  double* bufTvox = (double*)Tvox; 

  *Tx = (*bufTvox)*x; bufTvox++;
  *Tx += (*bufTvox)*y; bufTvox++;
  *Tx += (*bufTvox)*z; bufTvox++;
  *Tx += *bufTvox; bufTvox++;
  *Ty = (*bufTvox)*x; bufTvox++;
  *Ty += (*bufTvox)*y; bufTvox++;
  *Ty += (*bufTvox)*z; bufTvox++;
  *Ty += *bufTvox; bufTvox++;
  *Tz = (*bufTvox)*x; bufTvox++;
  *Tz += (*bufTvox)*y; bufTvox++;
  *Tz += (*bufTvox)*z; bufTvox++;
  *Tz += *bufTvox;

  return; 
}




/*
  axis == 0 -> source histogram
  axis == 1 -> target histogram 
  
  returns the sum of H 

*/
static double _marginalize(double* h, const double* H, int clampI, int clampJ, int axis)
{
  int i, j; 
  const double *bufH = H; 
  double *bufh = h;
  double hij, sumH = 0.0; 
  
  if (axis == 0) {
    memset((void*)h, 0, clampI*sizeof(double));
    for (i=0; i<clampI; i++, bufh++) 
      for (j=0; j<clampJ; j++, bufH++) {
	hij = *bufH; 
	sumH += hij; 
	*bufh += hij; 
      }
  }
  else if (axis == 1) {
    memset((void*)h, 0, clampJ*sizeof(double));
    for (j=0; j<clampJ; j++, bufh++) {
      bufH = H + j; 
      for (i=0; i<clampI; i++, bufH+=clampJ) {
	hij = *bufH; 
	sumH += hij; 
	*bufh += hij; 
      }
    }
  }
  
  return sumH; 
}




/* =========================================================================
   HISTOGRAM-BASED SIMILARITY MEASURES 
   ========================================================================= */

#define TINY 1e-30
#define NICELOG(x)((x)>(TINY) ? log(x):log(TINY)) 

static double _cc(const double* H, int clampI, int clampJ, double* n); 
static double _cr(const double* H, int clampI, int clampJ, double* n); 
static double _crL1(const double* H, double* hI, int clampI, int clampJ, double* n); 
static double _entropy(const double* h, size_t size, double* n); 
static double _mi(const double* H, double* hI, int clampI, double* hJ, int clampJ, double* n); 
static double _supervised_mi(const double* H, const double* F, 
			      double* fI, int clampI, double* fJ, int clampJ, 
			      double* n); 

double correlation_coefficient(const double* H, int clampI, int clampJ)
{
  double n; 
  return(_cc(H, clampI, clampJ, &n));
}

static double _cc(const double* H, int clampI, int clampJ, double* n)
{
  int i, j;
  double CC, mj, mi, mij, mj2, mi2, varj, vari, covij, na;
  double aux, auxj, auxi;
  const double *buf;

  /* Initialization */
  na = 0;
  mj  = 0;
  mi  = 0;
  mij = 0;
  mj2 = 0;
  mi2 = 0;
  
  /* Computes conditional moments */
  buf = H;
  for (i=0; i<clampI; i++) 
    for (j=0; j<clampJ; j++, buf++) {
      
      aux = *buf; /* aux == H(i,j) */
      auxj = j * aux;
      auxi = i * aux;
      
      na += aux;
      mj  += auxj;
      mi  += auxi;
      mj2 += j * auxj;
      mi2 += i * auxi;
      mij += i * auxj;
      
  }
  
  /* Test if the dataset is empty */
  if (na <= 0) {
    *n = 0; 
    return 0;
  }
  
  /* Normalization */
  mj  = mj / na;
  mi  = mi / na;
  mj2 = mj2 / na;
  mi2 = mi2 / na;
  mij = mij / na;
  
  /* Compute covariance and variance */
  covij = mij - mj * mi;
  covij = SQR(covij);
  varj  = mj2 - mj * mj;
  vari  = mi2 - mi * mi;
  aux = varj * vari;
  
  /* Check the variance product is non zero */
  if (aux <= 0) {
    *n = na;
    return 0;
  }
  
  /* Return the correlation coefficient */
  CC = covij / aux;
  
  *n = na; 
  return CC;
     
}


double correlation_ratio(const double* H, int clampI, int clampJ)
{
  double n; 
  return(_cr(H, clampI, clampJ, &n));
}

static double _cr(const double* H, int clampI, int clampJ, double* n)
{
  int i, j;
  double CR, na, mean, var, cvar, nJ, mJ, vJ, aux, aux2;
  const double *buf;

  /* Initialization */
  na = mean = var = cvar = 0;

  /* Compute conditional moments */
  for (j=0; j<clampJ; j++) {
    nJ = mJ = vJ = 0;
    buf = H + j;
    for (i=0; i<clampI; i++, buf+=clampJ) {
      aux = *buf; /* aux == H(j,i) */
      nJ += aux;
      aux2 = i*aux;
      mJ += aux2;
      vJ += i*aux2;
    }
    if (nJ>0) {
      na += nJ;
      mean += mJ;
      var += vJ;
      mJ /= nJ;
      vJ = vJ/nJ - mJ*mJ;
      cvar += nJ*vJ;
    }
  }
    
  /* Compute total moments */
  if (na <= 0) {
    *n = 0;
    return 0;
  }

  
  mean /= na;
  var = var/na - mean*mean;
  cvar /= na;

  /* Test on total variance */
  if (var<=0) {
    *n = na; 
    return 0;
  }
  
  /* Correlation ratio */
  *n = na; 
  CR = 1 - cvar/var;

  return CR;
  
}


double correlation_ratio_L1(const double* H, double* hI, int clampI, int clampJ)
{
  double n; 
  return(_crL1(H, hI, clampI, clampJ, &n));
}


static double _crL1(const double* H, double* hI, int clampI, int clampJ, double* n)
{
  int j;
  double na, med, dev, cdev, nJ, mJ, dJ;
   
  /* Initialization */
  na = cdev = 0;

  /* Compute conditional moments */  
  for (j=0; j<clampJ; j++) {
    _L1_moments (H+j, clampI, clampJ, &mJ, &dJ, &nJ);
    cdev += nJ*dJ;
    na += nJ;
  }
  
  /* Conditional dispersion */
  if (na <= 0.0) {
    *n = 0; 
    return 0.0;
  }
  cdev /= na;

  /* Total dispersion */
  _marginalize(hI, H, clampI, clampJ, 0); 
  _L1_moments (hI, clampI, 1, &med, &dev, &na);

  
  /* Test on total dispersion */
  *n = na; 
  if (dev==0.0)
    return 0.0;
  else
    return(1 - SQR(cdev)/SQR(dev)); /* Squaring for comparison with CR(L2) */  
}



double joint_entropy(const double* H, int clampI, int clampJ)
{
  double n; 
  double entIJ = _entropy(H, clampI*clampJ, &n); 
  return entIJ; 
}


double conditional_entropy(const double* H, double* hJ, int clampI, int clampJ)
{
  double n; 
  double entIJ, entJ;  
  _marginalize(hJ, H, clampI, clampJ, 1); 
  entIJ = _entropy(H, clampI*clampJ, &n); 
  entJ = _entropy(hJ, clampJ, &n); 
  return(entIJ - entJ); /* Entropy of I given J */ 
}


double mutual_information(const double* H, double* hI, int clampI, double* hJ, int clampJ)
{
  double n; 
  return(_mi(H, hI, clampI, hJ, clampJ, &n)); 
}

static double _mi(const double* H, double* hI, int clampI, double* hJ, int clampJ, double* n)
{
  double entIJ, entI, entJ; 
  _marginalize(hI, H, clampI, clampJ, 0); 
  _marginalize(hJ, H, clampI, clampJ, 1); 
  entI = _entropy(hI, clampI, n); 
  entJ = _entropy(hJ, clampJ, n); 
  entIJ = _entropy(H, clampI*clampJ, n); 
  return(entI + entJ - entIJ); 
}

/*
  Normalized mutual information as advocated by Studholme, 98. 

  NMI = 2*(1 - H(I,J)/[H(I)+H(J)])
  
*/

double normalized_mutual_information(const double* H, double* hI, int clampI, double* hJ, int clampJ)
{
  double n; 
  double entIJ, entI, entJ, aux; 
  _marginalize(hI, H, clampI, clampJ, 0); 
  _marginalize(hJ, H, clampI, clampJ, 1); 
  entI = _entropy(hI, clampI, &n); 
  entJ = _entropy(hJ, clampJ, &n); 
  entIJ = _entropy(H, clampI*clampJ, &n);
  aux = entI + entJ; 
  if (aux > 0.0) 
    return(2*(1-entIJ/aux));
  else 
    return 0.0; 
}


/*

Supervised mutual information. 
See Roche, PhD dissertation, University of Nice-Sophia Antipolis, 2001. 

*/ 

double supervised_mutual_information(const double* H, const double* F, 
				     double* fI, int clampI, double* fJ, int clampJ)
{
  double x, n; 
  x = _supervised_mi(H, F, fI, clampI, fJ, clampJ, &n); 
  if (n>0.0) 
    x /= n; 
  return(x); 
}


static double _supervised_mi(const double* H, const double* F, 
			      double* fI, int clampI, double* fJ, int clampJ, 
			      double* n)
{
  const double *bufH = H, *bufF = F; 
  double *buf_fI, *buf_fJ; 
  int i, j; 
  double hij, fij, fi, fj, aux, sumF, na = 0.0, SMI = 0.0; 

  sumF = _marginalize(fI, F, clampI, clampJ, 0); 
  sumF = _marginalize(fJ, F, clampI, clampJ, 1); 

  for (i=0, buf_fI=fI; i<clampI; i++, buf_fI++) {
    fi = *buf_fI / sumF; /* HACK to implicitely normalize F */ 
    for (j=0, buf_fJ=fJ; j<clampJ; j++, buf_fJ++, bufH++, bufF++) {
      hij = *bufH;
      na += hij;  
      fj = *buf_fJ;
      fij = *bufF;

      /* If fi=0 or fj=0, then fij = 0. We conventionally set
	 fij/(fi*fj) to zero but this might be problematic */ 
      aux = fi * fj; 
      if (aux > 0) 
	aux = fij / aux; 
      else 
	aux = 0.0;  
      SMI += hij * NICELOG(aux); 
    }
  }

  *n = na;
  return SMI; 
}



/* 
   First loop: compute the histogram sum 
   Second loop: compute actual entropy 
*/ 
static double _entropy(const double* h, size_t size, double* n)
{
  double E=0.0, sumh=0.0, aux; 
  size_t i; 
  double *buf;

  buf = (double*)h; 
  for (i=0; i<size; i++, buf++) 
    sumh += *buf; 

  if (sumh <= 0) {
    *n = 0; 
    return 0.0; 
  }

  buf = (double*)h; 
  for (i=0; i<size; i++, buf++) {
    aux = *buf / sumh; 
    E -= aux * NICELOG(aux); 
  }

  *n = sumh; 
  return E; 
}



static void _L1_moments (const double * h, int clamp, int stride, 
			  double* median, double* dev, double* sumh)

{
  int i, med;
  double sum, cpdf, lim, auxdev;
  const double *buf;

  /* Initialisation au cas ou */
  *median=0; *dev=0; *sumh=0;
  cpdf = sum = 0;
  
  buf = h;
  for (i=0; i<clamp; i++, buf+=stride) {
    sum += *buf;
  }
  
  *sumh = sum;
  
  if (sum == 0)
    return;
  
  /* On cherche la valeur i telle que h(i-1) < sum/2 
     et h(i) >= sum/2 */
  lim = 0.5*sum;
  
  i = 0;
  buf = h;
  cpdf = *buf;
  auxdev = 0;
  
  while (cpdf < lim) {
    i ++;
    buf += stride;
    cpdf += *buf;
    auxdev += - i*(*buf);
  }
  
  /* 
     On a alors i-1 < med < i. On prend i comme valeur mediane, 
     meme s'il serait possible de choisir une valeur intermediaire
     entre i-1 et i, en approchant la fonction de repartition 
     par une droite. 
     
     La dispersion L1 est donnee par :
     
     sum*E(|X-med|) = - sum_{i<=med} i h(i)              [1]
     
                      + sum_{i>med} i h(i)               [2]
     
                      + med * [2*cpdf(med) - sum]        [3]


     Le terme [1] est actuellement egal a la variable auxdev.
     Le terme cpdf(med) est actuellement egal a la var. cpdf.
  */
  
  *median = (double)i;
  auxdev += (2*cpdf - sum)*(*median);
  med = i+1;
  
  
  /* Pour achever le calcul de la deviation L1, il suffit de calculer 
     la moyenne tronquee (entre i et la dimension) (cf. [2]) */
  
  if (med < clamp) {
    buf = h + med*stride;
    for (i=med; i<clamp; i ++, buf += stride) 
      auxdev += i*(*buf);
  }
  
  *dev = auxdev/sum; 

  return;           
}



/* Tvox is the voxel transformation from source to target 
   Resample a 3d image undergoing an affine transformation. */
void cubic_spline_resample(PyArrayObject* im_resampled, 
			   const PyArrayObject* im, 
			   const double* Tvox)
{
  double i1;
  PyArrayObject* im_spline_coeff;
  PyArrayIterObject* imIter = (PyArrayIterObject*)PyArray_IterNew((PyObject*)im_resampled); 
  unsigned int x, y, z;
  unsigned dimX = PyArray_DIM(im, 0);
  unsigned dimY = PyArray_DIM(im, 1);
  unsigned dimZ = PyArray_DIM(im, 2);
  unsigned ddimX=dimX-1, ddimY=dimY-1, ddimZ=dimZ-1; 
  npy_intp dims[3] =  {dimX, dimY, dimZ}; 
  double Tx, Ty, Tz;

  /* Compute the spline coefficient image */
  im_spline_coeff = (PyArrayObject*)PyArray_SimpleNew(3, dims, NPY_DOUBLE);
  cubic_spline_transform(im_spline_coeff, im);

  /* Resampling loop */
  while(imIter->index < imIter->size) {
    x = imIter->coordinates[0];
    y = imIter->coordinates[1]; 
    z = imIter->coordinates[2]; 
    _apply_affine_transform(&Tx, &Ty, &Tz, Tvox, x, y, z); 
    if ((Tx<0) || (Tx>ddimX) ||
	(Ty<0) || (Ty>ddimY) ||
	(Tz<0) || (Tz>ddimZ))
      i1 = 0.0; 
    else 
      i1 = cubic_spline_sample3d(Tx, Ty, Tz, im_spline_coeff); 

    PyArray_SETITEM(im_resampled, PyArray_ITER_DATA(imIter), PyFloat_FromDouble(i1)); 
    PyArray_ITER_NEXT(imIter); 
  }

  /* Free memory */
  Py_DECREF(imIter);
  Py_DECREF(im_spline_coeff); 
    

  return;
	 
}


