/*****************************************************************************/
/*                                                                           */
/*    Copyright (C) -                              - All rights reserved     */
/*                                                                           */
/*****************************************************************************/
/*                                                                           */
/*  Except if expressly provided in a dedicated License Agreement, you are   */
/*  not authorized to:                                                       */
/*                                                                           */
/*  1. Use, copy, modify or transfer this software component, module or      */
/*  product, including any accompanying electronic or paper documentation    */
/*  (together, the "Software").                                              */
/*                                                                           */
/*  2. Remove any product identification, copyright, proprietary notices or  */
/*  labels from the Software.                                                */
/*                                                                           */
/*  3. Modify, reverse engineer, decompile, disassemble or otherwise attempt */
/*  to reconstruct or discover the source code, or any parts of it, from the */
/*  binaries of the Software.                                                */
/*                                                                           */
/*  4. Create derivative works based on the Software (e.g. incorporating the */
/*  Software in another software or commercial product or service without a  */
/*  proper license).                                                         */
/*                                                                           */
/*  By installing or using the "Software", you confirm your acceptance of the*/
/*  hereabove terms and conditions.                                          */
/*                                                                           */
/*****************************************************************************/


/*****************************************************************************/
/*  History:                                                                 */
/*****************************************************************************/
/*  Date       * Author          * Changes                                   */
/*****************************************************************************/
/*  2016-11-03 * Ricky Gong      * Creation of the file                      */
/*             *                 *                                           */
/*****************************************************************************/


/*****************************************************************************/
/*                                                                           */
/*  Include Files                                                            */
/*                                                                           */
/*****************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/aes.h>
#include <openssl/evp.h>
#include <openssl/bio.h>
#include <openssl/buffer.h> 
#include "AESApi.h"


/*****************************************************************************/
/*                                                                           */
/*  Definitions                                                              */
/*                                                                           */
/*****************************************************************************/


/*****************************************************************************/
/*                                                                           */
/*  Variable Declarations                                                    */
/*                                                                           */
/*****************************************************************************/
static unsigned char aeskey[AES_BLOCK_SIZE];


/*****************************************************************************/
/*                                                                           */
/*  Function Declarations                                                    */
/*                                                                           */
/*****************************************************************************/


/*****************************************************************************/
/*                                                                           */
/*  Function Implementations                                                 */
/*                                                                           */
/*****************************************************************************/
static char* Base64Encode(const char* input, int length, char* output, int* outlength)
{
    if((input == NULL) || (output == NULL) || (outlength == NULL))
        return NULL;

    BIO* bmem = NULL;
    BIO* b64 = NULL;
    BUF_MEM* bptr = NULL;

    b64 = BIO_new(BIO_f_base64());
    if(b64 == NULL)
        return NULL;
    bmem = BIO_new(BIO_s_mem());
    if(bmem == NULL)
        return NULL;
    b64 = BIO_push(b64, bmem);
    BIO_write(b64, input, length);
    BIO_flush(b64);
    BIO_get_mem_ptr(b64, &bptr);

    memcpy(output, bptr->data, bptr->length);
    *outlength = bptr->length;

    BIO_free_all(bmem);
    //BIO_free_all(b64);

    return output;
}

static char* Base64Decode(char* input, int length, char* output, int* outlength)
{
    if((input == NULL) || (output == NULL) || (outlength == NULL))
        return NULL;

    BIO* b64 = NULL;
    BIO* bmem = NULL;
  
    b64 = BIO_new(BIO_f_base64());
    if(b64 == NULL)
        return NULL;
    bmem = BIO_new_mem_buf(input, length);
    if(bmem == NULL)
        return NULL;
    bmem = BIO_push(b64, bmem);
    *outlength = BIO_read(bmem, output, length);
  
    BIO_free_all(bmem);
    //BIO_free_all(b64);

    return output;
}

char *AESEncrypt(char *str)
{
    if(str == NULL)
        return NULL;

    // calculate the length of the AES calculation, the input string should be 8 bytes 
    // assigned
    AES_KEY stAESKey;
    // set AES key structure
    AES_set_encrypt_key(aeskey, AES_BLOCK_SIZE*8, &stAESKey);
    unsigned int lengthIn = strlen(str);
    // simulate AES PKCS5 padding here because openssl doesn't support this padding mode
    // pad the number of the insufficient bytes to 16 byte with the insufficieant number value
    unsigned int paddinglen = AES_BLOCK_SIZE - (lengthIn % AES_BLOCK_SIZE);
    lengthIn = ((lengthIn / AES_BLOCK_SIZE) + 1) * AES_BLOCK_SIZE;
    char *requestpadding = (char *)malloc(lengthIn);
    if(requestpadding != NULL)
    {
        memcpy(requestpadding, str, lengthIn-paddinglen);
        memset(&requestpadding[lengthIn-paddinglen], (unsigned char)paddinglen, paddinglen);
        // allocate buffer to store encrypted data
        char* encryptData = (char*)malloc(lengthIn);
        if(encryptData != NULL) 
        {
            unsigned char initVect[AES_BLOCK_SIZE];

            memset(&initVect, 0, sizeof(initVect));
            AES_cbc_encrypt((unsigned char*)requestpadding, (unsigned char*)encryptData, lengthIn, &stAESKey, initVect, AES_ENCRYPT);
            // calculate the base64 string length
            unsigned int lennew = lengthIn*4/3;
            switch(lengthIn*4%3) {
                case 1:
                    lennew = (lengthIn+2)*4/3;
                    break;

                case 2:
                    lennew = (lengthIn+1)*4/3;
                    break;

                case 0:
                default:
                    break;
            }
            // calculate the base64 string length with extra '\n' for each line attached
            lennew = lennew + lennew/64 + 1;
            char *encryptDataBase64 = (char*)malloc(lennew);
            if(encryptDataBase64 != NULL)
            {
                int outlen = 0;
                Base64Encode((char *)encryptData, lengthIn, encryptDataBase64, &outlen);
                // remove the last '\n'
                encryptDataBase64[outlen-1] = 0;

                return encryptDataBase64;
            } else {
                printf("Allocate encrypt data buffer error");
            }

            free(encryptData);
        } else {
            printf("Allocate encrypt data buffer error");
        }

        free(requestpadding);
    } else {
        printf("Allocate padding data buffer error");
    }

    return NULL;
}

char *AESDecrypt(char *base64)
{
    if(base64 == NULL)
        return NULL;

    // calculate the length of the AES calculation, the input string should be 8 bytes 
    // assigned
    AES_KEY stAESKey;
    // set AES key structure
    AES_set_encrypt_key(aeskey, AES_BLOCK_SIZE*8, &stAESKey);
    unsigned int outBase64Len = strlen(base64);
    char* encryptResponse = (char*)malloc(outBase64Len*6/8+8);
    if(encryptResponse != NULL) {
        int outlen = 0;
        char *base64line =  (char*)malloc(outBase64Len+1);
        if(base64line != NULL) {
            memcpy(base64line, base64, outBase64Len);
            base64line[outBase64Len] = '\n';
            Base64Decode(base64line, strlen(base64line), encryptResponse, &outlen);
            AES_set_decrypt_key(aeskey, AES_BLOCK_SIZE*8, &stAESKey);
            char* responseData = (char*)malloc(outlen+1);
            if(responseData != NULL) {
                unsigned char initVect[AES_BLOCK_SIZE];

                memset(&initVect, 0, sizeof(initVect));
                AES_cbc_encrypt((unsigned char*)encryptResponse, (unsigned char*)responseData, outlen, &stAESKey, initVect, AES_DECRYPT);
                // remove the AES PKCS5 padding bytes
                int paddingbytes = (responseData[outlen-1]<outlen) ? responseData[outlen-1]: outlen;
                responseData[outlen-paddingbytes] = 0;

                return responseData;
            } else {
                printf("Allocate encrypt data buffer error");
            }

            free(base64line);
        } else {
            printf("Allocate encrypt data buffer error");
        }

        free(encryptResponse);
    } else {
        printf("Allocate encrypt data buffer error");
    }

    return NULL;
}

void AESFreeMem(char *ptr)
{
    if(ptr != NULL)
    {
        free(ptr);
        ptr = NULL;
    }       
}